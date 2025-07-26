import os
import psycopg2
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

DB_URL = os.getenv(
    "SUPABASE_DB_URL",
    "postgresql://postgres.kjwaoszgsozsywhdxdnp:c97W0c52Zyh7jm4f@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
)

def get_conn():
    return psycopg2.connect(DB_URL, options='-c client_encoding=UTF8')

def get_cursor():
    conn = get_conn()
    return conn.cursor()

def init_db():
    cur = get_cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pdf_files (
            id SERIAL PRIMARY KEY,
            user_email TEXT NOT NULL,
            filename TEXT,
            file_url TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.connection.commit()
    cur.connection.close()
