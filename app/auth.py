from fastapi import APIRouter, HTTPException, Form
from passlib.hash import bcrypt
import jwt, os
from dotenv import load_dotenv
from app.db import get_cursor
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET", "secret")  # fallback if not set

@router.post("/register")
def register(email: str = Form(...), password: str = Form(...)):
    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hash(password)
    cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed))
    cur.connection.commit()
    return {"message": "User registered successfully"}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    cur = get_cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if not user or not bcrypt.verify(password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=5)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {"access_token": token}
