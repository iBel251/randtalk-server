from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import CallbackContext
from connect_db import User

async def start_chat(update: Update, context: CallbackContext, db) -> None:
    user_id = int(update.effective_user.id)  # Use int for user_id

    # Fetch user details from PostgreSQL
    user_data = db.query(User).filter(User.id == user_id).first()

    if user_data:
        if not user_data.phone:
            # Ask the user to share their phone number
            keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Your phone number is missing. Please share your contact number to proceed.",
                reply_markup=reply_markup
            )
        elif user_data.account_status != "complete":
            # Prompt the user to complete registration in the web app
            web_app_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Complete Registration", web_app=WebAppInfo(url="https://randtalk-18e41.web.app/"))]
            ])
            await update.message.reply_text(
                "Your registration is incomplete. Please complete it using the web app:",
                reply_markup=web_app_button
            )
        else:
            # Notify the user that their account is complete
            await update.message.reply_text("Your account is complete. You can now start chatting!")
    else:
        await update.message.reply_text("No account data found. Please register first.")
