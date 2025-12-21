import os
from fastapi import APIRouter, HTTPException, Response, Request
from app.models.auth import UnlockRequest, UnlockResponse, LockResponse, StatusResponse
from app.core.crypto import validate_seed, derive_keys, generate_session_token
from app.core.database import init_database, set_vault_config, get_vault_config, set_active_db_key, DB_PATH

router = APIRouter(prefix="/api/auth", tags=["auth"])

#in-memory session store (I4: no session persistence)
sessions: dict[str, dict] = {}

@router.post("/unlock", response_model=UnlockResponse)
async def unlock_vault(request: UnlockRequest, response: Response):
    seed_phrase = request.seed_phrase.strip()
    if not validate_seed(seed_phrase):
        raise HTTPException(status_code=400, detail="Invalid seed phrase")
    #check if first-time unlock (no db file exists)
    first_unlock = not DB_PATH.exists()
    if first_unlock:
        #generate new salt for new vault
        salt = os.urandom(32)
        salt_hex = salt.hex()
    else:
        #existing vault: try to read salt with TEST_KEY first
        #(salt was stored before we had derived key)
        salt_hex = get_vault_config('salt')
        if salt_hex is None:
            #fallback: generate new salt
            salt = os.urandom(32)
            salt_hex = salt.hex()
        else:
            salt = bytes.fromhex(salt_hex)
    #derive keys from seed
    keys = derive_keys(seed_phrase, salt)
    #init db with derived key and store salt
    init_database(keys['db_key'])
    set_vault_config('salt', salt_hex, keys['db_key'])
    set_active_db_key(keys['db_key'])
    #create session
    session_token = generate_session_token()
    sessions[session_token] = {
        'db_key': keys['db_key'],
        'session_key': keys['session_key']
    }
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600
    )
    return UnlockResponse(status="success", message="Vault unlocked")

@router.post("/lock", response_model=LockResponse)
async def lock_vault(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token and session_token in sessions:
        del sessions[session_token]
    set_active_db_key(None)
    response.delete_cookie("session_token")
    return LockResponse(status="success", message="Vault locked")

@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request):
    session_token = request.cookies.get("session_token")
    unlocked = session_token is not None and session_token in sessions
    return StatusResponse(unlocked=unlocked)
