from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from datetime import datetime, timezone

from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.db.models.user_model import User as UserModel
from app.schemas import token_schema, user_schema
from app.services.google_oauth_service import GoogleOAuthService, get_google_oauth_service

router = APIRouter()

@router.post("/google", response_model=token_schema.Token, summary="Google OAuth2 Login/Registration")
async def login_via_google(
    request_data: token_schema.GoogleLoginRequest,
    db: AsyncSession = Depends(deps.get_db_session),
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    Autentikasi pengguna menggunakan Google.
    Client mengirim `server_auth_code` (direkomendasikan) atau `google_access_token`.
    Backend menukar kode/memverifikasi token, membuat atau mengambil user,
    lalu mengeluarkan JWT access dan refresh token internal aplikasi.
    """
    google_user_info: dict | None = None
    google_refresh_token_from_provider: str | None = None # Refresh token DARI GOOGLE
    
    # --- DEBUGGING: Cek data dari client ---
    print("\n--- DEBUG: REQUEST BODY YANG SEBENARNYA DARI FLUTTER ---")
    print(request_data.model_dump_json(indent=2))
    print("-------------------------------------------------------\n")
    # --- AKHIR DEBUGGING ---

    if request_data.server_auth_code:
        google_tokens = await google_service.exchange_auth_code(request_data.server_auth_code)
        
        # --- DEBUGGING: Cek pertukaran google token ---
        # print("\n--- DEBUG: MENGECEK GOOGLE TOKEN YANG DITUKAR ---")
        # print(google_tokens)
        # --- AKHIR DEBUGGING ---
        
        if not google_tokens or not google_tokens.get("access_token") or not google_tokens.get("id_token"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Google auth code or missing tokens.")
        
        google_access_token = google_tokens["access_token"]
        id_token = google_tokens["id_token"]
        google_refresh_token_from_provider = google_tokens.get("refresh_token") # Simpan ini jika perlu akses offline API Google
        
        # --- DEBUGGING: Cek akses token, id token, dan refresh token ---
        # print("\n--- DEBUG: MENDAPATKAN ACCESS TOKEN, ID TOKEN, DAN REFRESH TOKEN ---")
        # print(google_access_token)
        # print(id_token)
        # print(google_refresh_token_from_provider)
        # --- AKHIR DEBUGGING ---
        
        google_user_info = await google_service.get_user_info_from_google_tokens(id_token=id_token, google_access_token=google_access_token)

        # --- DEBUGGING: Cek User Info ---
        # print("\n--- DEBUG: MENDAPATKAN USER INFO ---")
        # print(google_user_info)
        # --- AKHIR DEBUGGING ---

    elif request_data.google_access_token:
        # Jika client hanya mengirim access token Google (kurang aman untuk refresh token Google)
        # Verifikasi dulu token ini dan dapatkan info pengguna
        verified_token_info = await google_service.verify_google_access_token_minimal(request_data.google_access_token)
        if not verified_token_info or not verified_token_info.get("sub"): # 'sub' adalah Google ID
             # Coba fallback ke userinfo endpoint jika tokeninfo tidak cukup
             google_user_info = await google_service.get_user_info_from_google_tokens(google_access_token=request_data.google_access_token)
        else:
            google_user_info = { # Ambil data dari token_info
                "email": verified_token_info.get("email"),
                "sub": verified_token_info.get("sub"),
                "name": verified_token_info.get("name") or verified_token_info.get("given_name"),
                "name": verified_token_info.get("name") or verified_token_info.get("given_name"),
                "picture": verified_token_info.get("picture"),
                "email_verified": verified_token_info.get("email_verified"),
            }
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either 'server_auth_code' or 'google_access_token' must be provided.")

    if not google_user_info or not google_user_info.get("sub") or not google_user_info.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user information from Google.")

    # --- LANGKAH DEBUGGING PENTING ---
    # Cetak data yang diterima router dari service
    # print("\n--- DEBUG: DATA DITERIMA OLEH ROUTER ---")
    # print(google_user_info)
    # print("----------------------------------------\n")
    # --- AKHIR LANGKAH DEBUGGING ---

    g_id = google_user_info["sub"]
    g_email = google_user_info["email"]
    g_name = google_user_info.get("name") # Mengambil 'name'
    g_picture = google_user_info.get("picture") # Mengambil 'picture'

    user = await crud_user.get_user_by_google_id(db, google_id=g_id)
    if not user:
        user = await crud_user.get_user_by_email(db, email=g_email)
        if user:
            update_data = {"google_id": g_id, "name": g_name, "picture": g_picture}
            user = await crud_user.update_user(db, user=user, data_to_update=update_data)
        else:
            user_in_create = user_schema.UserCreateGoogle(
                email=g_email,
                name=g_name, # Memastikan 'name' yang sudah diekstrak dimasukkan
                picture=g_picture, # Memastikan 'picture' yang sudah diekstrak dimasukkan
                google_id=g_id,
                google_refresh_token=google_refresh_token_from_provider
            )
            
            # --- DEBUGGING: Membuat user baru ---
            print(f"DEBUG ROUTER: Membuat user baru dengan data: {user_in_create.model_dump_json(indent=2)}")
            # --- AKHIR DEBUGGING ---
            
            user = await crud_user.create_google_user(db, user_in=user_in_create)

    elif google_refresh_token_from_provider and user.google_refresh_token != google_refresh_token_from_provider:
        # User sudah ada dengan google_id, update google_refresh_token jika berbeda/baru
        user = await crud_user.update_user(db, user=user, data_to_update={"google_refresh_token": google_refresh_token_from_provider})


    if not user or not user.id: # Safety check
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get or create user.")

    # Buat JWT internal
    # 'sub' untuk token internal sebaiknya adalah ID user di database Anda
    internal_access_token = security.create_access_token(subject=user.id)
    internal_refresh_token = security.create_refresh_token(subject=user.id)

    # Simpan hash dari refresh token internal ke user
    # Ini penting agar bisa di-revoke atau divalidasi
    refresh_token_hash = security.get_password_hash(internal_refresh_token)
    user = await crud_user.update_user(db, user=user, data_to_update={"internal_refresh_token_hash": refresh_token_hash})
    
    if not user: # Safety check setelah update terakhir
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user with refresh token hash.")


    return token_schema.Token(
        access_token=internal_access_token,
        refresh_token=internal_refresh_token
    )

@router.post("/refresh", response_model=token_schema.Token, summary="Refresh Access Token")
async def refresh_access_token(
    request_data: token_schema.RefreshTokenRequest,
    db: AsyncSession = Depends(deps.get_db_session),
):
    refresh_token = request_data.refresh_token
    token_payload = security.verify_jwt_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token_payload or not token_payload.sub:
        raise credentials_exception
    
    # Pastikan token ini adalah refresh token (jika Anda menambahkan klaim 'type' saat pembuatan)
    # if token_payload.type != "refresh":
    #     raise credentials_exception

    try:
        user_id = int(token_payload.sub)
    except ValueError:
        raise credentials_exception

    user = await crud_user.get_user_by_id(db, user_id=user_id)
    if not user or not user.internal_refresh_token_hash:
        raise credentials_exception
    
    if not security.verify_password(refresh_token, user.internal_refresh_token_hash):
        # Jika hash tidak cocok, mungkin token lama atau sudah dicabut/diganti
        # Hapus hash token dari DB sebagai tindakan keamanan tambahan
        await crud_user.update_user(db, user=user, data_to_update={"internal_refresh_token_hash": None})
        raise credentials_exception
        
    new_access_token = security.create_access_token(subject=user.id)
    
    # Opsional: Implementasikan rolling refresh tokens (buat refresh token baru juga)
    # new_refresh_token = security.create_refresh_token(subject=user.id)
    # new_refresh_token_hash = security.get_password_hash(new_refresh_token)
    # await crud_user.update_user(db, user=user, data_to_update={"internal_refresh_token_hash": new_refresh_token_hash})
    # return token_schema.Token(access_token=new_access_token, refresh_token=new_refresh_token)
    
    return token_schema.Token(access_token=new_access_token, refresh_token=refresh_token) # Kembalikan refresh token lama jika tidak rolling

@router.post("/logout", summary="Logout User")
async def logout_user(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user) # Memastikan user terautentikasi
):
    """
    Logout pengguna dengan menghapus hash refresh token internal mereka.
    Membutuhkan access token yang valid di header.
    """
    await crud_user.update_user(db, user=current_user, data_to_update={"internal_refresh_token_hash": None})
    return {"message": "Successfully logged out"}