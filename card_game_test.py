import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

# In-memory storage for card games
active_card_games = {}

suits = ["♠️", "♥️", "♦️", "♣️"]
values = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]

def generate_deck():
    return [f"{value}{suit}" for value in values for suit in suits]

def deal_hand(deck, n=9):
    random.shuffle(deck)
    return deck[:n], deck[n:]

async def card_test_handler(update: Update, context: CallbackContext) -> None:
    # Always use the Telegram user ID for both message and callback contexts
    user_id = update.effective_user.id if update.effective_user else (update.callback_query.from_user.id if update.callback_query else None)
    if not user_id:
        await update.message.reply_text("Could not determine user ID.")
        return
    deck = generate_deck()
    hand, remaining_deck = deal_hand(deck)
    # Store in memory
    active_card_games[user_id] = {"hand": hand, "deck": remaining_deck}
    hand_str = " ".join(hand)
    draw_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Draw", callback_data="card_draw")]
    ])
    # Use the correct method depending on context
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(f"🃏 Your hand: {hand_str}", reply_markup=draw_keyboard)
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(f"🃏 Your hand: {hand_str}", reply_markup=draw_keyboard)

async def card_draw_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    game = active_card_games.get(user_id)
    if not game:
        await query.answer()
        await query.edit_message_text("No game in progress. Click Card Match to start.")
        return
    hand = game["hand"]
    deck = game["deck"]
    if not deck:
        await query.answer()
        await query.edit_message_text("No more cards in the deck!")
        return
    drawn = deck.pop(random.randrange(len(deck)))
    hand.append(drawn)
    hand_str = " ".join(hand)
    draw_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Draw", callback_data="card_draw")]
    ])
    await query.answer()
    await query.edit_message_text(f"You drew: {drawn}\nYour hand: {hand_str}", reply_markup=draw_keyboard)
