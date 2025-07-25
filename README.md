
# PDF AI Bot with Supabase Auth + B2 + Gemini

## Features
- 🔐 Supabase-based Registration/Login
- 📁 PDF upload to Backblaze B2 (per user)
- 📚 Gemini learns from user's own PDFs only
- 🚫 Isolated storage per user

## Setup
1. Clone repo
2. Create `.env` file from `.env.example`
3. Run `pip install -r requirements.txt`
4. Run using `uvicorn main:app --reload`
