import os
import psycopg2
from urllib.parse import urlparse

def get_conn():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))


def get_cursor():
    conn = get_conn()
    cur = conn.cursor()
    cur.connection = conn  # attach connection for commit
    return cur

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
