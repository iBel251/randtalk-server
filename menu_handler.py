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
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        webapp_url = f"https://randtalk-18e41.web.app/earn/{user_id}"
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Open Web App to Earn Points", url=webapp_url)]
        ])
        await query.answer()
        await query.edit_message_text(
            "To earn points, open the web app:",
            reply_markup=inline_keyboard
        )
    elif query.data == "menu_edit_preferences":
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        webapp_url = f"https://randtalk-18e41.web.app/{user_id}"
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Open Web App to Edit Preferences", url=webapp_url)]
        ])
        await query.answer()
        await query.edit_message_text(
            "To edit your preferences, use the web app:",
            reply_markup=inline_keyboard
        )
    else:
        await query.answer()
        await query.edit_message_text("Unknown menu option.")
