import os
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

TEAM_SIZE = 6
MAX_PLAYERS = 24
FILLER_NAMES = [f"Rand{i+1}" for i in range(6)]

# Temporary storage in memory
user_data = {}

# Entry point
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send a list of players (like:\n1.Jimmy\n2.Alex\n3.Ben...)")

# Main message handler
async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_lines = update.message.text.strip().split("\n")
    players = parse_players(raw_lines)

    if len(players) > MAX_PLAYERS:
        await update.message.reply_text(f"❌ Too many players ({len(players)}). Max allowed is {MAX_PLAYERS}.")
        return

    players = complete_team_list(players)
    user_data[update.effective_user.id] = players
    await send_teams(update, context, players)

# Parse lines like "1. Jimmy", or just "Jimmy"
def parse_players(raw_lines):
    players = []
    for line in raw_lines:
        match = re.match(r'^\s*\d+\.\s*(.*)$', line)
        if match:
            name = match.group(1).strip()
        else:
            name = line.strip()
        if name:
            players.append(name)
    return players

# Fill players to multiple of 6 using Rand1, Rand2...
def complete_team_list(players):
    count = len(players)
    while count % TEAM_SIZE != 0 and count < MAX_PLAYERS:
        players.append(FILLER_NAMES[count % TEAM_SIZE])
        count += 1
    return players

# Create and shuffle teams
def create_teams(players):
    random.shuffle(players)
    num_teams = len(players) // TEAM_SIZE
    return [players[i * TEAM_SIZE:(i + 1) * TEAM_SIZE] for i in range(num_teams)]

# Send the team list with buttons
async def send_teams(update: Update, context: ContextTypes.DEFAULT_TYPE, players):
    teams = create_teams(players)
    text = "\n\n".join([f"🏆 Team {i + 1}:\n" + "\n".join(team) for i, team in enumerate(teams)])

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data="approve"),
            InlineKeyboardButton("🔁 Reshuffle", callback_data="reshuffle")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Handle both /start and button press
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

# Handle button clicks
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    players = user_data.get(user_id, [])

    if query.data == "approve":
        # ✅ Edit the existing message to show "Approved" at the top, keep the team list
        original_text = query.message.text
        approved_text = "✅ Teams approved!\n\n" + original_text
        await query.edit_message_text(approved_text)

    elif query.data == "reshuffle":
        # 🔁 Remove the old message and send a fresh one
        await query.delete_message()
        await send_teams(update, context, players)

        
# Main entry for Railway
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_list))
    app.add_handler(CallbackQueryHandler(handle_button))

    app.run_polling()

if __name__ == "__main__":
    main()
