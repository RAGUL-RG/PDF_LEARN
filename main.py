# main.py
import os
import time
import logging
import requests
import mysql.connector
import fitz  # PyMuPDF
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

UPLOAD_DIR = "uploads"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "ROOT"),
    "database": os.getenv("DB_NAME", "pdf_ai")
}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def connect_db(retries=5, delay=2):
    for i in range(retries):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            logger.error(f"Database connection attempt {i+1} failed: {err}")
            time.sleep(delay)
    raise ConnectionError("Could not connect to the database after multiple retries.")

def create_tables():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS pdf_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255),
            filepath VARCHAR(255),
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT,
            answer TEXT,
            asked_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Table creation failed: {e}")

@app.on_event("startup")
def startup_event():
    create_tables()

def ask_gemini(question, context):
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": f"Context: {context}\n\nQuestion: {question}"}]}]}
    try:
        res = requests.post(f"{endpoint}?key={GEMINI_API_KEY}", json=data, headers=headers)
        res.raise_for_status()
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "Gemini API error"

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    new_name = f"{uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, new_name)
    with open(path, "wb") as buffer:
        buffer.write(file.file.read())
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)", (file.filename, path))
    conn.commit()
    conn.close()
    return {"status": "success", "file_path": path}

@app.post("/ask")
async def ask(question: str = Form(...)):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM pdf_files ORDER BY uploaded_at DESC LIMIT 3")
    rows = cur.fetchall()
    context = ""
    for row in rows:
        try:
            with fitz.open(row[0]) as doc:
                for page in doc:
                    context += page.get_text()
        except:
            continue
    answer = ask_gemini(question, context[:20000])
    cur.execute("INSERT INTO questions (question, answer) VALUES (%s, %s)", (question, answer))
    conn.commit()
    conn.close()
    return {"answer": answer}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return HTMLResponse("""
        <html><head><title>PDF AI Bot</title></head>
        <body>
        <h2>Use /upload and /ask via Postman or frontend app.</h2>
        </body></html>
    """)
