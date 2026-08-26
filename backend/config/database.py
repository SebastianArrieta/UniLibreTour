import os
import psycopg
from contextlib import contextmanager


def get_connection():
    return psycopg.connect(os.getenv('DATABASE_URL'))


@contextmanager
def get_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                rol VARCHAR(20) DEFAULT 'visitante',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
