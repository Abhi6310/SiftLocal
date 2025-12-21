import secrets
from mnemonic import Mnemonic
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

mnemo = Mnemonic("english")

def generate_seed() -> str:
    #12 words = 128 bits entropy
    return mnemo.generate(strength=128)

def validate_seed(seed_phrase: str) -> bool:
    if not seed_phrase or not seed_phrase.strip():
        return False
    return mnemo.check(seed_phrase)

def derive_keys(seed_phrase: str, salt: bytes) -> dict:
    #argon2id: OWASP recommended params
    master_key = hash_secret_raw(
        secret=seed_phrase.encode('utf-8'),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID
    )
    #derive separate keys for db and session
    db_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b'siftlocal-db-key'
    ).derive(master_key)
    session_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b'siftlocal-session-key'
    ).derive(master_key)
    return {
        'db_key': db_key.hex(),
        'session_key': session_key.hex()
    }

def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
