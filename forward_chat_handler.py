from telegram import Update
from telegram.ext import CallbackContext
from connect_db import get_db, Chat

def get_partner_id(db, sender_id):
    # Ensure the `sender_id` is passed as an integer to match the database type
    sender_id = int(sender_id)

    # Fetch the chat record where the sender is matched
    chat = db.query(Chat).filter(
        (Chat.user_id == sender_id) | (Chat.partner_id == sender_id),
        Chat.status == "matched"
    ).first()

    if chat:
        # Determine the partner ID based on the sender's role in the chat
        if chat.user_id == sender_id:
            return chat.partner_id
        elif chat.partner_id == sender_id:
            return chat.user_id
    return None

async def forward_message(update: Update, context: CallbackContext) -> None:
    user_id = int(update.effective_user.id)
    message = update.message

    # Fetch the database session
    db = next(get_db())

    # Get the partner ID
    partner_id = get_partner_id(db, user_id)

    if not partner_id:
        await update.message.reply_text("You are not currently matched with any partner.")
        return

    # Ensure the message is not sent back to the sender
    if partner_id == user_id:
        await update.message.reply_text("Error: Cannot send messages to yourself.")
        return

    # Forward the message to the partner
    if message.text:
        await context.bot.send_message(chat_id=partner_id, text=message.text)
    elif message.photo:
        await context.bot.send_photo(chat_id=partner_id, photo=message.photo[-1].file_id, caption=message.caption)
    elif message.video:
        await context.bot.send_video(chat_id=partner_id, video=message.video.file_id, caption=message.caption)
    elif message.document:
        await context.bot.send_document(chat_id=partner_id, document=message.document.file_id, caption=message.caption)
    elif message.audio:
        await context.bot.send_audio(chat_id=partner_id, audio=message.audio.file_id, caption=message.caption)
    elif message.voice:
        await context.bot.send_voice(chat_id=partner_id, voice=message.voice.file_id, caption=message.caption)
    elif message.video_note:
        await context.bot.send_video_note(chat_id=partner_id, video_note=message.video_note.file_id)
    elif message.sticker:
        await context.bot.send_sticker(chat_id=partner_id, sticker=message.sticker.file_id)
    else:
        await update.message.reply_text("Unsupported message type. Only text, photos, videos, audio, voice, video notes, stickers, and documents can be forwarded.")