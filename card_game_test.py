import redis
import random
from telegram import Update
from telegram.ext import CallbackContext

# Connect to Redis (default settings for local dev)
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

suits = ["♠️", "♥️", "♦️", "♣️"]
values = ["A"] + [str(n) for n in range(2, 11)] + ["J", "Q", "K"]

def generate_deck():
    return [f"{value}{suit}" for value in values for suit in suits]

def deal_hand(deck, n=9):
    random.shuffle(deck)
    return deck[:n], deck[n:]

async def card_test_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    # Generate a deck and deal a hand
    deck = generate_deck()
    hand, remaining_deck = deal_hand(deck)
    # Store hand in Redis for this user
    r.set(f"testgame:{user_id}:hand", ",".join(hand))
    r.set(f"testgame:{user_id}:deck", ",".join(remaining_deck))
    hand_str = " ".join(hand)
    await update.message.reply_text(f"🃏 Your hand: {hand_str}\n(Type /draw to draw a card)")

async def card_draw_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    hand = r.get(f"testgame:{user_id}:hand")
    deck = r.get(f"testgame:{user_id}:deck")
    if not hand or not deck:
        await update.message.reply_text("No game in progress. Type /cardtest to start.")
        return
    hand = hand.split(",")
    deck = deck.split(",")
    if not deck:
        await update.message.reply_text("No more cards in the deck!")
        return
    drawn = deck.pop(0)
    hand.append(drawn)
    r.set(f"testgame:{user_id}:hand", ",".join(hand))
    r.set(f"testgame:{user_id}:deck", ",".join(deck))
    hand_str = " ".join(hand)
    await update.message.reply_text(f"You drew: {drawn}\nYour hand: {hand_str}")
