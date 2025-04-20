from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from connect_db import get_db, User

async def menu_handler(update: Update, context: CallbackContext) -> None:
    inline_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("My Points", callback_data="menu_my_points"),
            InlineKeyboardButton("Earn Points", callback_data="menu_earn_points")
        ],
        [
            InlineKeyboardButton("Edit Preferences", callback_data="menu_edit_preferences")
        ]
    ])
    await update.message.reply_text(
        "Menu:\nChoose an option:",
        reply_markup=inline_keyboard
    )

async def menu_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.from_user.id)
    db = next(get_db())
    if query.data == "menu_my_points":
        user = db.query(User).filter(User.id == user_id).first()
        points = user.points if user and user.points is not None else 0
        await query.answer()
        await query.edit_message_text(f"You have {points} points.")
    elif query.data == "menu_earn_points":
        await query.answer()
        await query.edit_message_text("To earn points, invite friends or complete tasks (feature coming soon).")
    elif query.data == "menu_edit_preferences":
        await query.answer()
        await query.edit_message_text("To edit your preferences, use the web app or send /start to update your info.")
    else:
        await query.answer()
        await query.edit_message_text("Unknown menu option.")
