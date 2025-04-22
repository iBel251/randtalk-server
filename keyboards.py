from telegram import ReplyKeyboardMarkup, KeyboardButton

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Search Partner")],
        [KeyboardButton("Menu")],
        [KeyboardButton("Play Games")]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)

SEARCH_PARTNER_KEYBOARD = MAIN_MENU_KEYBOARD

CANCEL_WAITING_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Cancel Waiting")],
        [KeyboardButton("Menu")],
        [KeyboardButton("Play Games")]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)

END_CHAT_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("End Chat")],
        [KeyboardButton("Menu")],
        [KeyboardButton("Play Games")]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)
