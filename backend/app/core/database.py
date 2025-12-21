import os
from pathlib import Path
from pysqlcipher3 import dbapi2 as sqlite

#use env var for path, default to local data/ for dev
DB_PATH = Path(os.environ.get("SIFTLOCAL_DB_PATH", "data/siftlocal.db"))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

#test key for development (replaced by derived key in production)
TEST_KEY = "test-key-for-c03-only"

#active db key - set by auth on unlock
_active_db_key: str | None = None

def set_active_db_key(key: str | None):
    global _active_db_key
    _active_db_key = key

def get_active_db_key() -> str | None:
    return _active_db_key

def get_connection(db_key: str | None = None):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite.connect(str(DB_PATH))
    key = db_key or _active_db_key or TEST_KEY
    conn.execute(f"PRAGMA key = '{key}'")
    return conn

def init_database(db_key: str | None = None):
    conn = get_connection(db_key)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def get_tables(db_key: str | None = None):
    conn = get_connection(db_key)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_vault_config(key: str, db_key: str | None = None) -> str | None:
    conn = get_connection(db_key)
    cursor = conn.execute("SELECT value FROM vault_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_vault_config(key: str, value: str, db_key: str | None = None):
    conn = get_connection(db_key)
    conn.execute(
        "INSERT OR REPLACE INTO vault_config (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def get_preference(key: str, db_key: str | None = None) -> str | None:
    conn = get_connection(db_key)
    cursor = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_preference(key: str, value: str, db_key: str | None = None):
    conn = get_connection(db_key)
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()
