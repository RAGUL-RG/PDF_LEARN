from fastapi import APIRouter, Form, Depends
from app.db import get_cursor
from app.utils import get_user_email
from app.gemini import ask_gemini
import fitz
import requests

router = APIRouter()

@router.post("/")
def ask_question(question: str = Form(...), user_email: str = Depends(get_user_email)):
    cur = get_cursor()
    cur.execute("SELECT file_url FROM pdf_files WHERE user_email = %s", (user_email,))
    files = cur.fetchall()
    context = ""
    for (url,) in files:
        pdf = requests.get(url)
        with open("temp.pdf", "wb") as f:
            f.write(pdf.content)
        doc = fitz.open("temp.pdf")
        for page in doc:
            context += page.get_text()
    return {"answer": ask_gemini(question, context[:20000])}