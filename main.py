# main.py
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import mysql.connector
from datetime import datetime
import fitz  # PyMuPDF
from uuid import uuid4
import logging
import requests
import time

# === LOGGING === #
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

# === CONFIG === #
UPLOAD_DIR = "uploads"

# Ensure the uploads folder exists BEFORE mount
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),  # Changed from 'db' to 'localhost' for local development
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "ROOT"),
    "database": os.getenv("DB_NAME", "pdf_ai")
}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key")

# === DATABASE SETUP === #
def connect_db(retries=5, delay=2):
    for i in range(retries):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            logger.error(f"Database connection attempt {i+1} failed: {err}")
            time.sleep(delay)
    raise ConnectionError("Could not connect to the database after multiple retries.")

def create_table():
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255),
                filepath VARCHAR(255),
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT,
                answer TEXT,
                asked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Table creation failed: {e}")

@app.on_event("startup")
def startup_event():
    create_table()

# === HELPER FUNCTIONS === #
def save_file(file: UploadFile):
    ext = file.filename.split(".")[-1]
    new_filename = f"{uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)",
                    (file.filename, file_path))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save file info to DB: {e}")

    return file_path

def extract_text_from_pdf(file_path):
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        logger.error(f"PDF extraction failed for {file_path}: {e}")
    return text

# === GEMINI INTEGRATION === #
def ask_gemini(question, context):
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [
                {"text": f"Context: {context}\n\nQuestion: {question}"}
            ]
        }]
    }
    try:
        response = requests.post(f"{endpoint}?key={GEMINI_API_KEY}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.RequestException as e:
        logger.error(f"Gemini API request failed: {e}")
        return "Sorry, I couldn't get a response from Gemini."
    except (KeyError, IndexError) as e:
        logger.error(f"Unexpected Gemini API response: {e}")
        return "Sorry, the response format from Gemini was unexpected."

# === ROUTES === #
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        file_path = save_file(file)
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        logger.exception("File upload failed.")
        return {"status": "error", "message": "Upload failed. Please try again."}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT filepath FROM pdf_files ORDER BY uploaded_at DESC LIMIT 3")
        rows = cur.fetchall()

        context = ""
        for row in rows:
            context += extract_text_from_pdf(row[0]) + "\n"

        response = ask_gemini(question, context[:20000])  # keep context within token limit

        cur.execute("INSERT INTO questions (question, answer) VALUES (%s, %s)", (question, response))
        conn.commit()
        conn.close()

        return JSONResponse({"answer": response})
    except Exception as e:
        logger.exception("An error occurred while answering the question.")
        return JSONResponse({"answer": "Something went wrong while processing your question."}, status_code=500)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF AI Bot</title>
    </head>
    <body>
        <h1>Upload PDFs</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <button type="submit">Upload</button>
        </form>

        <h2>Ask a Question</h2>
        <form id="askForm">
            <input type="text" name="question" placeholder="Type your question...">
            <button type="submit">Ask</button>
        </form>
        <p><strong>Answer:</strong> <span id="answer"></span></p>

        <script>
            document.getElementById("askForm").onsubmit = async (e) => {
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const res = await fetch("/ask", {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();
                document.getElementById("answer").innerText = data.answer;
            }
        </script>
    </body>
    </html>
    """
