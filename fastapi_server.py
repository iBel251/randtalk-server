from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

def register_handlers():
    async def start(update: Update, context: CallbackContext) -> None:
        try:
            user = update.effective_user
            user_id = int(user.id)
            db = next(get_db())
            user_data = db.query(User).filter(User.id == user_id).first()

            # Check for referral in /start command
            if update.message and update.message.text:
                match = re.match(r"/start ref_(\d+)", update.message.text)
                if match and not user_data:
                    referrer_id = int(match.group(1))
                    referrer = db.query(User).filter(User.id == referrer_id).first()
                    if referrer:
                        referrer.points = (referrer.points or 0) + 10
                        db.commit()
                        await context.bot.send_message(chat_id=referrer_id, text=f"🎉 You earned 10 points for inviting a new user!")
            await update.message.reply_text("Welcome to RandTalket! Use the menu to navigate.")
        except Exception as e:
            print(f"Error in start handler: {e}")
    
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
async def handle_contact(update: Update, context: CallbackQueryHandler):
    contact = update.message.contact
    user_id = int(contact.user_id)
    db = next(get_db())
    user_data = db.query(User).filter(User.id == user_id).first()
    if user_data:
        user_data.phone = contact.phone_number
        user_data.account_status = "phoneShared"
        db.commit()
        await update.message.reply_text("Thank you for sharing your phone number! Please complete your registration using the integrated web app.")
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
        web_app_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Complete Registration", web_app=WebAppInfo(url=f"https://randtalk-18e41.web.app/{user_id}"))]
        ])
        await update.message.reply_text(
            "Click the button below to complete your registration:",
            reply_markup=web_app_button
        )
        search_partner_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Search Partner")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await update.message.reply_text(
            "You can now search for a partner!",
            reply_markup=search_partner_keyboard
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
