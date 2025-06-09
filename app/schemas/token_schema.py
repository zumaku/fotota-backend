from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject of the token (usually user ID or email)")
    type: Optional[str] = None      # Untuk membedakan tipe token, misal 'event_access'
    event_id: Optional[int] = None  # Untuk menyimpan ID event di dalam token

class GoogleLoginRequest(BaseModel):
    # Client akan mengirim salah satu dari ini:
    server_auth_code: Optional[str] = Field(None, description="Google Server Auth Code (recommended)")
    google_access_token: Optional[str] = Field(None, description="Google Access Token (fallback)")

class RefreshTokenRequest(BaseModel):
    refresh_token: str