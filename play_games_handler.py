from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext
from card_game_test import card_test_handler

async def play_games_handler(update: Update, context: CallbackContext) -> None:
    games_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Card Match", callback_data="game_card_match")]
    ])
    await update.message.reply_text(
        "🎮 <b>Welcome to Play Games!</b>\n\n"
        "💰 <b>Use your points to play games, win more points, and (soon) cash out to real money!</b>\n"
        "💸 <i>Cashout feature coming soon!</i>\n\n"
        "👇 <b>Choose a game to start:</b>",
        reply_markup=games_keyboard,
        parse_mode="HTML"
    )
