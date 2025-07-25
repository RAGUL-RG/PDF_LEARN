import psycopg2, os

def get_conn():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_DB_HOST"),
        user=os.getenv("SUPABASE_DB_USER"),
        password=os.getenv("SUPABASE_DB_PASS"),
        database=os.getenv("SUPABASE_DB_NAME"),
        port=5432
    )

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
