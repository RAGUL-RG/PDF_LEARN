from fastapi import FastAPI
from app.auth import router as auth_router
from app.db import init_db
from app.upload import router as upload_router
from app.ask import router as ask_router

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router, prefix="/auth")
app.include_router(upload_router, prefix="/upload")
app.include_router(ask_router, prefix="/ask")

@app.get("/")
def root():
    return {"message": "PDF AI Bot API Running"}