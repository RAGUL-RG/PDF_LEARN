from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from app.utils import upload_to_b2, get_user_id_from_token, supabase_client

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    authorization: str = Header(..., alias="Authorization")
):
    try:
        user_id = get_user_id_from_token(authorization)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or missing token")

        # Optional: You can enforce PDF only
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        file_url = upload_to_b2(file, user_id)

        insert_response = supabase_client.table("pdfs").insert({
            "user_id": user_id,
            "file_name": file.filename,
            "file_url": file_url
        }).execute()

        if insert_response.get("error"):
            raise HTTPException(status_code=500, detail="Failed to insert record in Supabase")

        return {"status": "success", "url": file_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
