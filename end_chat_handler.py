from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from connect_db import get_db, Chat
from keyboards import END_CHAT_KEYBOARD, CANCEL_WAITING_KEYBOARD

def end_chat_in_db(db, user_id):
    """Remove both the user's and their partner's chat records from the database."""
    # Fetch the chat record where the user is matched
    chat = db.query(Chat).filter(
        (Chat.user_id == user_id) | (Chat.partner_id == user_id),
        Chat.status == "matched"
    ).first()

    if not chat:
        return None

    # Determine the partner ID
    partner_id = chat.partner_id if chat.user_id == user_id else chat.user_id

    # Remove both chat records
    db.query(Chat).filter(Chat.user_id == user_id, Chat.partner_id == partner_id).delete()
    db.query(Chat).filter(Chat.user_id == partner_id, Chat.partner_id == user_id).delete()
    db.commit()

    return partner_id

async def end_chat(update: Update, context: CallbackContext) -> None:
    user_id = int(update.effective_user.id)

    # Fetch the database session
    db = next(get_db())

    # End the chat in the database
    partner_id = end_chat_in_db(db, user_id)

    if not partner_id:
        await update.message.reply_text("You are not currently in an active chat.")
        return

    # Notify both users
    await update.message.reply_text(
        "The chat has been terminated. You can now search for a new partner.",
        reply_markup=END_CHAT_KEYBOARD
    )
    await context.bot.send_message(
        chat_id=partner_id,
        text="The chat has been terminated by your partner. You can now search for a new partner.",
        reply_markup=END_CHAT_KEYBOARD
    )

async def cancel_waiting(update: Update, context: CallbackContext) -> None:
    user_id = int(update.effective_user.id)

    # Fetch the database session
    db = next(get_db())

    # Remove the user's waiting record from the database
    waiting_chat = db.query(Chat).filter(Chat.user_id == user_id, Chat.status == "waiting").first()
    if not waiting_chat:
        await update.message.reply_text("You are not currently in the waiting list.")
        return

    db.query(Chat).filter(Chat.user_id == user_id, Chat.status == "waiting").delete()
    db.commit()

    # Notify the user
    await update.message.reply_text(
        "You have been removed from the waiting list. You can now search for a partner again.",
        reply_markup=CANCEL_WAITING_KEYBOARD
    )