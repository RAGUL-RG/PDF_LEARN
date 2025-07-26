from fastapi import APIRouter, UploadFile, File, Depends
import os
from uuid import uuid4
from app.b2 import upload_pdf_to_b2
from app.utils import get_user_email
from app.db import get_cursor

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...), user_email: str = Depends(get_user_email)):
    # Generate unique filename
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid4().hex}.{ext}"

    # Save to temp folder
    os.makedirs("temp", exist_ok=True)
    local_path = os.path.join("temp", unique_name)
    with open(local_path, "wb") as f:
        f.write(await file.read())

    # Upload to Backblaze B2
    b2_url = upload_pdf_to_b2(local_path, unique_name)

    # Delete local temp file
    os.remove(local_path)

    # Insert file info into database
    cur = get_cursor()
    cur.execute(
        "INSERT INTO pdf_files (user_email, filename, file_url) VALUES (%s, %s, %s)",
        (user_email, file.filename, b2_url)
    )
    cur.connection.commit()
    cur.connection.close()

    return {"url": b2_url, "status": "Uploaded successfully"}
