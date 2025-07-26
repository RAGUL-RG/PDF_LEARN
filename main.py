from fastapi import FastAPI
from app.auth import router as auth_router
from app.db import init_db
from app.upload import router as upload_router
from app.ask import router as ask_router

app = FastAPI()

# Initialize database connection on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Register routers with prefixes
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(ask_router, prefix="/ask", tags=["Ask"])

# Root endpoint
@app.get("/")
def root():
    return {"message": "✅ PDF AI Bot API is running!"}
