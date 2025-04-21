from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from connect_db import get_db, User, Chat as Chats, UserUpdate
from start_chat_handler import start_chat
from search_partner_handler import search_partner
from forward_chat_handler import forward_message
from end_chat_handler import end_chat, cancel_waiting
from menu_handler import menu_handler, menu_callback_handler
from dotenv import load_dotenv
from telegram_auth import router as telegram_auth_router
from sqlalchemy import or_
import re
import base64

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

app = FastAPI()

# CORS for your webapp and local dev
origins = [
    "https://randtalk-18e41.web.app",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .concurrent_updates(True)
    .build()
)

def safe_base64_decode(s):
    s = s.strip().replace(' ', '').replace('\n', '')
    missing_padding = len(s) % 4
    if missing_padding:
        s += '=' * (4 - missing_padding)
    return base64.urlsafe_b64decode(s).decode()

def register_handlers():
    async def start(update: Update, context: CallbackContext) -> None:
        try:
            user = update.effective_user
            user_id = int(user.id)
            db = next(get_db())
            user_data = db.query(User).filter(User.id == user_id).first()

            # Check for referral in /start command (only for new users)
            if update.message and update.message.text:
                match = re.match(r"/start ref_([A-Za-z0-9_-]+)", update.message.text)
                if match and not user_data:
                    encoded_referrer = match.group(1)
                    try:
                        referrer_id = int(safe_base64_decode(encoded_referrer))
                        referrer = db.query(User).filter(User.id == referrer_id).first()
                        if referrer:
                            referrer.points = (referrer.points or 0) + 10
                            db.commit()
                            await context.bot.send_message(chat_id=referrer_id, text=f"🎉 You earned 10 points for inviting a new user!")
                    except Exception as e:
                        print(f"Referral decode error: {e}")

            # Registration and onboarding logic
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

            # Default: Show main menu
            main_menu_keyboard = ReplyKeyboardMarkup(
                [
                    [KeyboardButton("Search Partner")],
                    [KeyboardButton("Menu")]
                ],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await update.message.reply_text(
                "Welcome back! Your account is complete. Enjoy using the bot!",
                reply_markup=main_menu_keyboard
            )
        except Exception as e:
            print(f"Error in start handler: {e}")
            if update.message:
                await update.message.reply_text("An error occurred. Please try again later.")
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Start Chat$"), lambda u, c: start_chat(u, c, next(get_db()))))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Search Partner$"), search_partner))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^End Chat$"), end_chat))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Cancel Waiting$"), cancel_waiting))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Menu$"), menu_handler))
    application.add_handler(CallbackQueryHandler(menu_callback_handler, pattern="^menu_"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/user/{user_id}")
def fetch_user(user_id: int):
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
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
    }

@app.put("/user/{user_id}")
def update_user(user_id: int, data: UserUpdate):
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    return {"message": "User data updated successfully"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    tg_update = Update.de_json(update, application.bot)
    await application.process_update(tg_update)
    return JSONResponse(content={"ok": True})

# Handler for contact sharing (must be async for FastAPI)
async def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    user_id = int(contact.user_id)
    db = next(get_db())
    user_data = db.query(User).filter(User.id == user_id).first()
    if user_data:
        user_data.phone = contact.phone_number
        user_data.account_status = "phoneShared"
        db.commit()
        # Send a single, clear message with the web app button
        web_app_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Complete Registration", web_app=WebAppInfo(url=f"https://randtalk-18e41.web.app/{user_id}"))]
        ])
        await update.message.reply_text(
            "Thank you for sharing your phone number! Please complete your registration using the button below:",
            reply_markup=web_app_button
        )

@app.on_event("startup")
async def on_startup():
    register_handlers()
    await application.initialize()
    await application.bot.set_webhook(
        f"{WEBHOOK_URL}/webhook",
        drop_pending_updates=True,
        allowed_updates=["message", "edited_message", "callback_query", "chat_member", "my_chat_member"]
    )
    await application.start()

app.include_router(telegram_auth_router)
