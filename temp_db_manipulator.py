from connect_db import get_db, Chat, User

def clear_chats_table():
    """Remove all data from the chats table."""
    db = next(get_db())
    db.query(Chat).delete()
    db.commit()
    print("All data from the chats table has been removed.")

def remove_user_by_name(name):
    """Remove a user from the users table by name."""
    db = next(get_db())
    db.query(User).filter(User.name == name).delete()
    db.commit()
    print(f"User with name '{name}' has been removed from the users table.")

def remove_chat_by_user_id(user_id):
    """Remove a chat record from the chats table by user_id."""
    db = next(get_db())
    db.query(Chat).filter(Chat.user_id == user_id).delete()
    db.commit()
    print(f"Chat record with user_id '{user_id}' has been removed from the chats table.")

if __name__ == "__main__":
    # clear_chats_table()
    # Example usage: Remove user with name 'Imran'
    remove_user_by_name("Imran")
    # Example usage: Remove chat with user_id 344468363
    #remove_chat_by_user_id(344468363)