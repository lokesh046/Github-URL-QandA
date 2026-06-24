import os
import sqlite3
from config import DATABASE_URL

# PostgreSQL specific connection pool
_postgres_pool = None


def get_db_pool():
    global _postgres_pool
    if DATABASE_URL and _postgres_pool is None:
        from psycopg_pool import ConnectionPool
        from psycopg.rows import dict_row

        def check_conn(conn):
            conn.execute("SELECT 1;")

        print("[Database] Initializing shared Postgres connection pool...")
        _postgres_pool = ConnectionPool(
            conninfo=DATABASE_URL,
            max_size=6,
            timeout=10.0,
            check=check_conn,
            kwargs={
                "autocommit": True, 
                "row_factory": dict_row,
                "connect_timeout": 5
            }
        )
    return _postgres_pool


def get_db_connection():
    if DATABASE_URL:
        pool = get_db_pool()
        return pool.connection()
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_dir = os.path.join(project_root, "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "users.db")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn 


def close_db_pool():
    global _postgres_pool
    if _postgres_pool:
        print("[Database] Closing shared Postgres connection pool...")
        try:
            _postgres_pool.close()
        except Exception as e:
            print(f"Error closing pool: {e}")
        _postgres_pool = None


def init_db():
    if DATABASE_URL:
        try:
            with get_db_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS qa_users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        hashed_password VARCHAR(255) NOT NULL
                    );
                """)
                # Alter to add email column if it doesn't exist
                try:
                    conn.execute("ALTER TABLE qa_users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;")
                except Exception:
                    pass
            print("[Database] Postgres qa_users table initialized.")
        except Exception as e:
            print(f"Error initializing Postgres database: {e}")
    else:
        try:
            conn = get_db_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS qa_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        hashed_password TEXT NOT NULL
                    );
                """)
                conn.commit()
                # Alter to add email column if it doesn't exist
                try:
                    conn.execute("ALTER TABLE qa_users ADD COLUMN email TEXT UNIQUE;")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
            finally:
                conn.close()
            print("[Database] SQLite qa_users table initialized.")
        except Exception as e:
            print(f"Error initializing SQLite database: {e}")


def get_user_by_username(username: str):
    if DATABASE_URL:
        with get_db_connection() as conn:
            result = conn.execute(
                "SELECT id, username, email, hashed_password FROM qa_users WHERE username = %s OR email = %s;",
                (username, username)
            ).fetchone()
            return dict(result) if result else None
    else:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            result = cursor.execute(
                "SELECT id, username, email, hashed_password FROM qa_users WHERE username = ? OR email = ?;",
                (username, username)
            ).fetchone()
            return dict(result) if result else None
        finally:
            conn.close()


def get_user_by_email(email: str):
    if DATABASE_URL:
        with get_db_connection() as conn:
            result = conn.execute(
                "SELECT id, username, email, hashed_password FROM qa_users WHERE email = %s;",
                (email,)
            ).fetchone()
            return dict(result) if result else None
    else:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            result = cursor.execute(
                "SELECT id, username, email, hashed_password FROM qa_users WHERE email = ?;",
                (email,)
            ).fetchone()
            return dict(result) if result else None
        finally:
            conn.close()


def create_user(username: str, email: str, hashed_password: str) -> bool:
    try:
        if DATABASE_URL:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO qa_users (username, email, hashed_password) VALUES (%s, %s, %s);",
                    (username, email, hashed_password)
                )
                return True
        else:
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO qa_users (username, email, hashed_password) VALUES (?, ?, ?);",
                    (username, email, hashed_password)
                )
                conn.commit()
                return True
            finally:
                conn.close()
    except Exception as e:
        print(f"Error creating user in DB: {e}")
        return False
