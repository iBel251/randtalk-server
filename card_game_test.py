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

def start_card_game_for_user(user_id):
    deck = generate_deck()
    hand, remaining_deck = deal_hand(deck)
    active_card_games[user_id] = {"hand": hand, "deck": remaining_deck}
    return hand

def get_draw_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Draw", callback_data="card_draw")]
    ])

async def card_test_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    hand = start_card_game_for_user(user_id)
    hand_str = " ".join(hand)
    await update.message.reply_text(f"🃏 Your hand: {hand_str}", reply_markup=get_draw_keyboard())

async def card_match_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    hand = start_card_game_for_user(user_id)
    hand_str = " ".join(hand)
    await query.edit_message_text(f"🃏 Your hand: {hand_str}", reply_markup=get_draw_keyboard())

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
    await query.answer()
    await query.edit_message_text(f"You drew: {drawn}\nYour hand: {hand_str}", reply_markup=get_draw_keyboard())
