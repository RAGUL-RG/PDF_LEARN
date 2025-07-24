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

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# === CONFIG === #
UPLOAD_DIR = "uploads"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "ROOT"),
    "database": os.getenv("DB_NAME", "pdf_ai")
}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAgITtZxIu4YQf9by4tXBelVJogJd5brtE")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# === DATABASE SETUP === #
def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def create_table():
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
    conn.commit()
    conn.close()

create_table()

# === HELPER FUNCTIONS === #
def save_file(file: UploadFile):
    ext = file.filename.split(".")[-1]
    new_filename = f"{uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO pdf_files (filename, filepath) VALUES (%s, %s)",
                (file.filename, file_path))
    conn.commit()
    conn.close()

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
        conn.close()

        context = ""
        for row in rows:
            context += extract_text_from_pdf(row[0]) + "\n"

        response = ask_gemini(question, context[:20000])  # keep context within token limit
        return JSONResponse({"answer": response})
    except Exception as e:
        logger.exception("An error occurred while answering the question.")
        return JSONResponse({"answer": "Something went wrong while processing your question."}, status_code=500)

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
