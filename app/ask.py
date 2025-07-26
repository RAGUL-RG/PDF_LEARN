from fastapi import APIRouter, Form, Depends, HTTPException
from app.db import get_cursor
from app.utils import get_user_email
from app.gemini import ask_gemini
import fitz  # PyMuPDF
import requests
import os

router = APIRouter()

@router.post("/")
def ask_question(
    question: str = Form(...),
    user_email: str = Depends(get_user_email)
):
    # Get user's uploaded PDF URLs
    cur = get_cursor()
    cur.execute("SELECT file_url FROM pdf_files WHERE user_email = %s", (user_email,))
    files = cur.fetchall()

    if not files:
        raise HTTPException(status_code=404, detail="No PDFs found for this user.")

    # Extract text from each PDF
    context = ""
    for (url,) in files:
        try:
            response = requests.get(url)
            response.raise_for_status()

            with open("temp.pdf", "wb") as f:
                f.write(response.content)

            with fitz.open("temp.pdf") as doc:
                for page in doc:
                    context += page.get_text()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process PDF from {url}. Error: {str(e)}")

    # Truncate context to 20,000 characters for performance
    context = context[:20000]

    # Use Gemini to answer the question
    answer = ask_gemini(question, context)

    # Cleanup temporary file
    if os.path.exists("temp.pdf"):
        os.remove("temp.pdf")

    return {"answer": answer}
