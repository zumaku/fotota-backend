from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from fastapi import Path
from app.core import security
from app.core.config import settings
from app.db.database import get_db_session # Diganti dari database.py
from app.crud import crud_user
from app.db.models.user_model import User as UserModel
from app.schemas.token_schema import TokenPayload

# OAuth2PasswordBearer menunjuk ke endpoint yang akan mengeluarkan token (meskipun kita tidak pakai form password)
# Ini hanya untuk FastAPI mengenali skema Bearer token di Swagger UI.
# Endpoint token kita sebenarnya adalah /auth/google atau /auth/refresh
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/auth/google" # Sesuaikan dengan prefix API Anda jika ada
)

async def get_current_user(
    db: AsyncSession = Depends(get_db_session), token: str = Depends(reusable_oauth2)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_payload = security.verify_jwt_token(token, settings.JWT_SECRET_KEY)
    if not token_payload or not token_payload.sub: # sub biasanya user_id
        print("Token verification failed or sub missing from token_payload.")
        raise credentials_exception
    
    try:
        user_id = int(token_payload.sub) # Asumsi 'sub' adalah user ID (integer)
    except ValueError:
        print(f"Token 'sub' is not a valid integer: {token_payload.sub}")
        raise credentials_exception # Atau error spesifik lain

    user = await crud_user.get_user_by_id(db, user_id=user_id)
    if not user:
        print(f"User not found for id: {user_id} from token.")
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    # Jika ada field is_active di model User, Anda bisa cek di sini
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Dependensi untuk memeriksa apakah pengguna yang sedang login adalah seorang admin.
    Jika bukan, akan melempar error 403 Forbidden.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_event_access_payload(
    event_id: int = Path(...), # Ambil event_id dari path URL
    token: str = Depends(reusable_oauth2) # Ambil token dari header Authorization
) -> TokenPayload:
    """
    Dependensi untuk melindungi endpoint galeri.
    Memastikan token yang diberikan adalah Event Access Token yang valid
    untuk event_id yang spesifik.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, # 403 Forbidden lebih cocok daripada 401
        detail="You do not have access to this event gallery",
    )
    
    # Verifikasi token menggunakan secret key khusus event
    payload = security.verify_jwt_token(token, settings.JWT_EVENT_SECRET_KEY)
    
    # Ekstrak klaim dari payload
    # Kita akan menyimpan 'type' dan 'event_id' di dalam token
    token_type = payload.type if payload else None
    token_event_id = payload.event_id if payload else None

    # Lakukan validasi
    if not payload or token_type != "event_access" or token_event_id != event_id:
        raise credentials_exception
    
    return payload