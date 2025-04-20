import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from connect_db import get_db, User, Chat as Chats
from start_chat_handler import start_chat
from search_partner_handler import search_partner
from forward_chat_handler import forward_message
from end_chat_handler import end_chat, cancel_waiting
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# Load environment variables from .env file
load_dotenv()

# Replace hardcoded values with environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set this in Render's environment variables

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the Flask app
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://randtalk-18e41.web.app",
    "https://web.telegram.org",
    "https://abcd1234.ngrok.io",  # Replace with your actual ngrok URL
    "https://eb3a-2603-8000-ca00-88c"  # Added the current ngrok URL
]}}, supports_credentials=True)

@app.route('/')
def home():
    return "Welcome to the Telegram Bot Server!"

@app.route('/', methods=['POST'])
def telegram_webhook():
    print("Webhook endpoint called", flush=True)
    import asyncio
    import json
    try:
        update = request.get_json()
        print("Incoming update:", json.dumps(update, indent=2), flush=True)  # Log the incoming update
        if update:
            tg_update = Update.de_json(update, application.bot)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(tg_update))
    except Exception as e:
        print(f"Error in webhook endpoint: {e}", flush=True)
    return "", 200

@app.route('/user/<int:user_id>', methods=['GET'])
def fetch_user(user_id):
    """Fetch user data by ID."""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "phone": user.phone,
        "account_status": user.account_status,
        "preferences": user.preferences,
        "age": user.age,
        "city": user.city,
        "country": user.country,
        "gender": user.gender,
        "points": user.points,
        "status": user.status,
        "birthdate": user.birthdate
    })

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user data by ID."""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json

    # Update fields if provided in the request
    if "preferences" in data:
        user.preferences = data["preferences"]
    if "points" in data:
        user.points = data["points"]
    if "gender" in data:
        user.gender = data["gender"]
    if "birthdate" in data:
        user.birthdate = data["birthdate"]
    if "city" in data:
        user.city = data["city"]
    if "country" in data:
        user.country = data["country"]
    if "age" in data:
        user.age = data["age"]
    if "account_status" in data:
        user.account_status = data["account_status"]

    db.commit()

    return jsonify({"message": "User data updated successfully"})

def run_flask():
    """Run the Flask app in a separate thread."""
    port = int(os.getenv("PORT", 5000))  # Use the PORT environment variable or default to 5000
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Define the application object globally
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

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
    # Register the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Register a handler for shared contacts
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Register a handler for "Start Chat"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Start Chat$"), lambda u, c: start_chat(u, c, next(get_db()))))

    # Register a handler for "Search Partner"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Search Partner$"), search_partner))

    # Register a handler for "End Chat"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^End Chat$"), end_chat))

    # Register a handler for "Cancel Waiting"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Cancel Waiting$"), cancel_waiting))

    # Register a handler for forwarding messages between matched users
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Register all bot handlers
    main()

    # Set the webhook and initialize the application ONCE, synchronously, before entering the Flask loop
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.bot.set_webhook(WEBHOOK_URL))
    # Do NOT call asyncio.run() again or start another event loop!