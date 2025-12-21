import pytest
from app.core.crypto import generate_seed, validate_seed, derive_keys, generate_session_token

def test_generate_seed():
    seed = generate_seed()
    words = seed.split()
    assert len(words) == 12
    assert all(len(word) > 0 for word in words)

def test_validate_seed_valid():
    #known valid BIP39 test vector
    valid_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    assert validate_seed(valid_seed) is True

def test_validate_seed_invalid():
    assert validate_seed("invalid word list test") is False
    assert validate_seed("") is False
    assert validate_seed("   ") is False

def test_derive_keys():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    salt = b"test-salt-32-bytes-long-exactly!"
    keys = derive_keys(seed, salt)
    assert 'db_key' in keys
    assert 'session_key' in keys
    assert len(keys['db_key']) == 64  #32 bytes hex
    assert len(keys['session_key']) == 64
    assert keys['db_key'] != keys['session_key']

def test_derive_keys_deterministic():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    salt = b"test-salt-32-bytes-long-exactly!"
    keys1 = derive_keys(seed, salt)
    keys2 = derive_keys(seed, salt)
    assert keys1['db_key'] == keys2['db_key']
    assert keys1['session_key'] == keys2['session_key']

def test_derive_keys_different_salts():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    salt1 = b"salt1-32-bytes-long-exactly!!!!!"
    salt2 = b"salt2-32-bytes-long-exactly!!!!!"
    keys1 = derive_keys(seed, salt1)
    keys2 = derive_keys(seed, salt2)
    assert keys1['db_key'] != keys2['db_key']

def test_generate_session_token():
    token1 = generate_session_token()
    token2 = generate_session_token()
    assert len(token1) > 0
    assert token1 != token2
