
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from app.utils import upload_to_b2, get_user_id_from_token, supabase_client

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), authorization: str = Header(...)):
    user_id = get_user_id_from_token(authorization)
    file_url = upload_to_b2(file, user_id)
    supabase_client.table("pdfs").insert({
        "user_id": user_id,
        "file_name": file.filename,
        "file_url": file_url
    }).execute()
    return {"status": "success", "url": file_url}
