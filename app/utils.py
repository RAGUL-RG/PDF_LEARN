from fastapi import Header, HTTPException
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "secret")

# ✅ Get user email from JWT
def get_user_email(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded["email"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Get user ID from JWT (used in storage.py)
def get_user_id_from_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded["email"]  # or decoded["user_id"] if you store user_id in token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Supabase client (used in storage.py)
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Optional: Upload wrapper if you want to reuse
from app.b2 import upload_pdf_to_b2
from uuid import uuid4

def upload_to_b2(file: UploadFile, user_id: str):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"

    os.makedirs("temp", exist_ok=True)
    local_path = f"temp/{filename}"

    with open(local_path, "wb") as f:
        f.write(file.file.read())

    url = upload_pdf_to_b2(local_path, filename)
    os.remove(local_path)
    return url
