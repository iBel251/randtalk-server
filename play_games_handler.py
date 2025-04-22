from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from telegram.ext import CallbackContext

async def play_games_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    games_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Card Match", web_app=WebAppInfo(url=f"https://randtalk-18e41.web.app/cardmatch?user_id={user_id}"))]
    ])
    await update.message.reply_text(
        "🎮 <b>Welcome to Play Games!</b>\n\n"
        "💰 <b>Use your points to play games, win more points, and (soon) cash out to real money!</b>\n"
        "💸 <i>Cashout feature coming soon!</i>\n\n"
        "👇 <b>Choose a game to start:</b>",
        reply_markup=games_keyboard,
        parse_mode="HTML"
    )
