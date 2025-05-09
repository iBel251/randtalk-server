from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from connect_db import get_db, User, Chat as Chats
from datetime import datetime
from keyboards import END_CHAT_KEYBOARD, CANCEL_WAITING_KEYBOARD

# In-memory cache for active chat sessions
active_chats = {}

def find_match(db, user_id, preferences):
    # Parse preferences
    gender, age_range, city = preferences.split("/")
    # Handle 'any' for age as well
    if age_range.lower() == "any":
        min_age = max_age = None
    else:
        min_age, max_age = map(int, age_range.split("-")) if "-" in age_range else (None, None)

    # Build the query to find a match from the chats table
    query = db.query(Chats).join(User, Chats.user_id == User.id).filter(
        Chats.user_id != user_id,  # Exclude the current user
        Chats.status == "waiting"  # Only consider users who are waiting
    )

    # Only filter by gender if not 'any'
    if gender.lower() != "any":
        query = query.filter((User.gender == gender) | (User.gender == None))
    # Only filter by age if not 'any'
    if min_age is not None and max_age is not None:
        query = query.filter(User.age >= min_age, User.age <= max_age)
    # Only filter by city if not 'any'
    if city.lower() != "any":
        query = query.filter((User.city == city) | (User.city == None))

    # Return the first match
    return query.first()

async def search_partner(update: Update, context: CallbackContext) -> None:
    user_id = int(update.effective_user.id)

    # Fetch user details from PostgreSQL
    db = next(get_db())
    user_data = db.query(User).filter(User.id == user_id).first()

    if not user_data or not user_data.preferences:
        await update.message.reply_text("You need to set your preferences before searching for a partner.")
        return

    # Check if the user is already matched
    existing_matched_chat = db.query(Chats).filter(
        Chats.user_id == user_id, Chats.status == "matched"
    ).first()
    if existing_matched_chat:
        await update.message.reply_text("You are already matched with a partner. Start chatting with them!")
        return

    # Check if the user is already waiting
    existing_waiting_chat = db.query(Chats).filter(Chats.user_id == user_id, Chats.status == "waiting").first()
    if existing_waiting_chat:
        await update.message.reply_text("You are already in the waiting list. Please wait to be matched.")
        return

    # Find a match based on preferences
    match = find_match(db, user_id, user_data.preferences)

    if match:
        # Check if a chat session already exists between the two users
        existing_chat = db.query(Chats).filter(
            ((Chats.user_id == user_id) & (Chats.partner_id == match.id)) |
            ((Chats.user_id == match.id) & (Chats.partner_id == user_id))
        ).first()

        if existing_chat:
            await update.message.reply_text("You are already matched with this partner. Start chatting now!")
            return

        # Update the first waiting user's chat record
        waiting_chat = db.query(Chats).filter(Chats.user_id == match.user_id, Chats.status == "waiting").first()
        if waiting_chat:
            waiting_chat.partner_id = user_id
            waiting_chat.status = "matched"
            waiting_chat.updated_at = datetime.utcnow().isoformat()

        # Update the second user's chat record
        new_chat = Chats(
            user_id=user_id,
            partner_id=match.user_id,
            status="matched",
            preferences=user_data.preferences,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(new_chat)
        db.commit()

        # Store both users as active chat partners in the in-memory cache
        active_chats[user_id] = match.user_id
        active_chats[match.user_id] = user_id

        # Fetch the matched user's details
        matched_user = db.query(User).filter(User.id == match.user_id).first()

        # Notify both users and display the "End Chat", "Menu", and "Play Games" keyboard
        await update.message.reply_text(
            f"You have been matched with {matched_user.name}! Start chatting now.",
            reply_markup=END_CHAT_KEYBOARD
        )
        await context.bot.send_message(
            chat_id=match.user_id,
            text=f"You have been matched with {user_data.name}! Start chatting now.",
            reply_markup=END_CHAT_KEYBOARD
        )

        # Update the keyboard to show "End Chat", "Menu", and "Play Games" after a match is found
        await update.message.reply_text(
            "You are now matched! You can end the chat anytime.",
            reply_markup=END_CHAT_KEYBOARD
        )
        return

    else:
        # Add the user to the waiting list
        new_chat = Chats(
            user_id=user_id,
            status="waiting",
            preferences=user_data.preferences,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(new_chat)
        db.commit()

        # Display the "Cancel Waiting", "Menu", and "Play Games" button when the user is added to the waiting list
        await update.message.reply_text(
            "No match found at the moment. You have been added to the waiting list.",
            reply_markup=CANCEL_WAITING_KEYBOARD
        )