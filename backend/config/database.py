import os
import pymysql
import pymysql.cursors
from urllib.parse import urlparse
from contextlib import contextmanager


def get_connection():
    db_url = os.getenv('DATABASE_URL', 'mysql://museo:museo@localhost:3306/museo_db')
    url = urlparse(db_url)

    user = url.username or os.getenv('DB_USER', 'museo')
    password = url.password or os.getenv('DB_PASSWORD', 'museo')
    host = url.hostname or os.getenv('DB_HOST', 'localhost')
    port = url.port or int(os.getenv('DB_PORT', 3306))
    dbname = url.path.lstrip('/') or os.getenv('DB_NAME', 'museo_db')

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=dbname,
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor
    )


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
    try:
        with get_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    rol VARCHAR(20) DEFAULT 'visitante',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
    except Exception as e:
        print(f"Error inicializando la base de datos MySQL: {e}")

