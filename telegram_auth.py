import hmac
import hashlib
import time
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

BOT_TOKEN = "your-telegram-bot-token"

@router.post("/verify")
async def verify_telegram_auth(request: Request):
    body = await request.json()
    init_data = body.get("initData")
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing initData")

    # Compute the secret key
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()

    # Parse initData into key-value pairs
    data = dict(item.split("=") for item in init_data.split("&"))
    hash_from_telegram = data.pop("hash", None)

    # Sort and concatenate data for hashing
    sorted_data = "\n".join(f"{key}={data[key]}" for key in sorted(data.keys()))

    # Compute the hash
    computed_hash = hmac.new(secret_key, sorted_data.encode(), hashlib.sha256).hexdigest()

    # Compare the computed hash with the provided hash
    if computed_hash != hash_from_telegram:
        raise HTTPException(status_code=403, detail="Invalid hash")

    # Check the timestamp
    auth_date = int(data.get("auth_date", 0))
    current_time = int(time.time())
    if current_time - auth_date > 300:  # 5 minutes
        raise HTTPException(status_code=403, detail="Request expired")

    return {"success": True, "user": data}