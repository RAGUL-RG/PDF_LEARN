from fastapi import APIRouter, UploadFile, File, Depends
import os
from uuid import uuid4
from app.b2 import upload_pdf_to_b2
from app.utils import get_user_email
from app.db import get_cursor

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...), user_email: str = Depends(get_user_email)):
    ext = file.filename.split(".")[-1]
    name = f"{uuid4().hex}.{ext}"
    os.makedirs("temp", exist_ok=True)
    local_path = f"temp/{name}"
    with open(local_path, "wb") as f:
        f.write(file.file.read())
    b2_url = upload_pdf_to_b2(local_path, name)
    os.remove(local_path)
    cur = get_cursor()
    cur.execute("INSERT INTO pdf_files (user_email, filename, file_url) VALUES (%s, %s, %s)", (user_email, file.filename, b2_url))
    cur.connection.commit()
    cur.connection.close()
    return {"url": b2_url}