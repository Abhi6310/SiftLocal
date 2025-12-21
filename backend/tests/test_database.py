import pytest
from pathlib import Path
from app.core.database import (
    init_database,
    get_tables,
    get_vault_config,
    set_vault_config,
    get_preference,
    set_preference,
    DB_PATH
)

@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()

def test_init_database():
    init_database()
    assert DB_PATH.exists()

def test_schema_contract():
    #I4 compliance: only allowed tables
    init_database()
    tables = get_tables()
    allowed = {'vault_config', 'preferences'}
    assert set(tables) == allowed, f"Schema violation: {tables}"

def test_vault_config():
    init_database()
    set_vault_config('salt', 'test-salt-value')
    assert get_vault_config('salt') == 'test-salt-value'
    set_vault_config('salt', 'new-salt-value')
    assert get_vault_config('salt') == 'new-salt-value'
    assert get_vault_config('nonexistent') is None

def test_preferences():
    init_database()
    set_preference('theme', 'dark')
    assert get_preference('theme') == 'dark'
    set_preference('theme', 'light')
    assert get_preference('theme') == 'light'
    assert get_preference('nonexistent') is None

def test_no_session_tables():
    #I4 compliance: no forbidden tables
    init_database()
    tables = get_tables()
    forbidden = {'sessions', 'messages', 'documents', 'chat_history', 'prompts'}
    assert not forbidden.intersection(set(tables)), "Forbidden tables found"
