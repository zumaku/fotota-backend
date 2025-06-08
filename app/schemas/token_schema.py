from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject of the token (usually user ID or email)")
    # Anda bisa tambahkan klaim lain jika perlu, misalnya 'exp', 'iat', 'jti'
    # exp: Optional[int] = None
    # type: Optional[str] = None # Untuk membedakan access dan refresh token jika perlu

class GoogleLoginRequest(BaseModel):
    # Client akan mengirim salah satu dari ini:
    server_auth_code: Optional[str] = Field(None, description="Google Server Auth Code (recommended)")
    google_access_token: Optional[str] = Field(None, description="Google Access Token (fallback)")

class RefreshTokenRequest(BaseModel):
    refresh_token: str