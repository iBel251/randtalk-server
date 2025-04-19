from flask import Flask, request, jsonify
from connect_db import get_db, User

app = Flask(__name__)

@app.route('/user/<int:user_id>', methods=['GET'])
def fetch_user(user_id):
    """Fetch user data by ID."""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
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
    })

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user data by ID."""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json

    # Update fields if provided in the request
    if "preferences" in data:
        user.preferences = data["preferences"]
    if "points" in data:
        user.points = data["points"]

    db.commit()

    return jsonify({"message": "User data updated successfully"})

if __name__ == '__main__':
    app.run(debug=True)