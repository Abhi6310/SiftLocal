import os
from pathlib import Path
from pysqlcipher3 import dbapi2 as sqlite

#use env var for path, default to local data/ for dev
DB_PATH = Path(os.environ.get("SIFTLOCAL_DB_PATH", "data/siftlocal.db"))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

#test key for C03 (replaced with derived key in C05)
TEST_KEY = "test-key-for-c03-only"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite.connect(str(DB_PATH))
    conn.execute(f"PRAGMA key = '{TEST_KEY}'")
    return conn

def init_database():
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def get_tables():
    conn = get_connection()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_vault_config(key: str) -> str | None:
    conn = get_connection()
    cursor = conn.execute("SELECT value FROM vault_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_vault_config(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO vault_config (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def get_preference(key: str) -> str | None:
    conn = get_connection()
    cursor = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_preference(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()
