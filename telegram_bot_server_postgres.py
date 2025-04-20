import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from connect_db import get_db, User, Chat as Chats
from start_chat_handler import start_chat
from search_partner_handler import search_partner
from forward_chat_handler import forward_message
from end_chat_handler import end_chat, cancel_waiting

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

application = Application.builder() \
    .token(TELEGRAM_BOT_TOKEN) \
    .concurrent_updates(True)  # Telegram recommended for webhook \
    .post_init(None)           # Default, can be omitted \
    .build()

# Define the /start command handler
async def start(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user  # Get the user object
        user_id = int(user.id)  # Use int for user_id

        # Fetch user details from PostgreSQL
        db = next(get_db())
        user_data = db.query(User).filter(User.id == user_id).first()

        if not user_data:
            # New user: Ask for contact number
            keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Welcome! Please share your contact number to register.",
                reply_markup=reply_markup
            )
            # Save initial user details
            new_user = User(id=user_id, name=user.first_name, username=user.username, account_status="incomplete", phone=None)
            db.add(new_user)
            db.commit()
            return

        if not user_data.phone:
            # Ask for contact number if missing
            keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "Your phone number is missing. Please share your contact number to complete your registration.",
                reply_markup=reply_markup
            )
            return

        if user_data.account_status != "complete":
            # Add a button linking to the integrated web app
            web_app_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Complete Registration", web_app=WebAppInfo(url=f"https://randtalk-18e41.web.app/{user_id}"))]
            ])
            await update.message.reply_text(
                "Your account is incomplete. Please complete your registration using the integrated web app:",
                reply_markup=web_app_button
            )
            return

        # Determine the user's current status
        user_chat = db.query(Chats).filter(
            (Chats.user_id == user_id) | (Chats.partner_id == user_id)
        ).order_by(Chats.updated_at.desc()).first()

        if user_chat and user_chat.status == "matched":
            # Show "End Chat" button if the user is matched
            main_menu_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("End Chat")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await update.message.reply_text(
                "You are currently matched with a partner. You can end the chat.",
                reply_markup=main_menu_keyboard
            )
            return

        # Default: Show "Search Partner" button
        main_menu_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Search Partner")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "Welcome back! Your account is complete. Enjoy using the bot!",
            reply_markup=main_menu_keyboard
        )
    except Exception as e:
        print(f"Error in /start handler: {e}")
        if update.message:
            await update.message.reply_text("An error occurred. Please try again later.")

# Define a handler to process the shared contact
async def handle_contact(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact
    user_id = int(contact.user_id)  # Use int for user_id

    # Fetch user details from PostgreSQL
    db = next(get_db())
    user_data = db.query(User).filter(User.id == user_id).first()

    if user_data:
        # Update user data with the phone number and set account_status to phoneShared
        user_data.phone = contact.phone_number
        user_data.account_status = "phoneShared"
        db.commit()

        # Notify the user
        await update.message.reply_text("Thank you for sharing your phone number! Please complete your registration using the integrated web app.")
        
        # Add a button linking to the integrated web app
        web_app_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Complete Registration", web_app=WebAppInfo(url=f"https://randtalk-18e41.web.app/{user_id}"))]
        ])
        await update.message.reply_text(
            "Click the button below to complete your registration:",
            reply_markup=web_app_button
        )

        # Display the "Search Partner" button
        search_partner_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Search Partner")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "You can now search for a partner!",
            reply_markup=search_partner_keyboard
        )

def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Start Chat$"), lambda u, c: start_chat(u, c, next(get_db()))))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Search Partner$"), search_partner))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^End Chat$"), end_chat))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Cancel Waiting$"), cancel_waiting))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

if __name__ == "__main__":
    import asyncio
    async def main_async():
        main()
        await application.initialize()
        await application.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True, allowed_updates=["message", "edited_message", "callback_query", "chat_member", "my_chat_member"])  # Telegram recommended
        await application.start()
        await application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            allowed_updates=["message", "edited_message", "callback_query", "chat_member", "my_chat_member"]  # Telegram recommended
        )
    asyncio.run(main_async())