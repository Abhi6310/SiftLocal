from pydantic import BaseModel, Field

class UnlockRequest(BaseModel):
    seed_phrase: str = Field(..., min_length=1)

class UnlockResponse(BaseModel):
    status: str
    message: str

class LockResponse(BaseModel):
    status: str
    message: str

class StatusResponse(BaseModel):
    unlocked: bool
