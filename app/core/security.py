from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from app.schemas.token_schema import TokenPayload

# Konteks untuk hashing (misalnya untuk refresh token internal jika disimpan sebagai hash)
# Atau untuk password jika ada login email/password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_jwt_token(
    subject: Union[str, Any],
    expires_delta: timedelta,
    secret_key: str,
    additional_claims: Optional[dict] = None
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    if additional_claims:
        to_encode.update(additional_claims)
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(subject: Union[str, Any]) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_jwt_token(subject, expires_delta, settings.JWT_SECRET_KEY)

def create_refresh_token(subject: Union[str, Any]) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # Anda bisa menambahkan klaim 'type': 'refresh' jika ingin membedakan di payload
    return create_jwt_token(subject, expires_delta, settings.JWT_REFRESH_SECRET_KEY, {"type": "refresh"})

def verify_jwt_token(token: str, secret_key: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError: # Termasuk ExpiredSignatureError, JWTClaimsError, dll.
        return None

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)