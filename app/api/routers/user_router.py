# app/api/routers/user_router.py

import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models.user_model import User as UserModel
from app.schemas import user_schema
from app.crud import crud_user
from app.core.config import settings

# Tentukan path di mana Anda ingin menyimpan foto selfie di VM Anda
# Pastikan direktori ini ada dan FastAPI memiliki izin untuk menulis di sana.
# Contoh: /var/www/fotota/storage/selfies
os.makedirs(settings.SELFIE_STORAGE_PATH, exist_ok=True) # Buat direktori jika belum ada

router = APIRouter()

@router.get("/me", response_model=user_schema.UserPublic, summary="Get Current User Information")
async def read_current_user(
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Ambil informasi tentang pengguna yang saat ini terautentikasi.
    Flutter akan memanggil ini setelah login untuk memeriksa apakah 'selfie' null.
    """
    return current_user

@router.post("/me/selfie", response_model=user_schema.UserPublic, summary="Upload or Update User Selfie")
async def upload_or_update_selfie(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user),
    selfie_file: UploadFile = File(...)
):
    """
    Endpoint untuk mengunggah atau memperbarui foto selfie referensi pengguna.
    Jika foto selfie lama ada, file tersebut akan dihapus dan diganti dengan yang baru.
    """
    # 1. Validasi tipe file
    if selfie_file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a JPG, PNG, or WEBP image."
        )

    # 2. Hapus file selfie lama jika ada untuk menghemat ruang
    if current_user.selfie and os.path.exists(current_user.selfie):
        print(f"DEBUG: Deleting old selfie file: {current_user.selfie}")
        os.remove(current_user.selfie)

    # 3. Buat nama file yang unik untuk menghindari konflik
    file_extension = selfie_file.filename.split(".")[-1]
    unique_filename = f"user_{current_user.id}_{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(SELFIE_STORAGE_PATH, unique_filename)

    # 4. Simpan file baru secara asinkron
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await selfie_file.read(1024):  # Baca per-chunk
                await out_file.write(content)
        print(f"DEBUG: New selfie saved to: {file_path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )

    # 5. Update path file di database
    # Di sini kita hanya menyimpan path lokal. Untuk URL publik, Anda perlu logika tambahan
    # yang menggabungkan base URL Nginx Anda, contoh:
    public_url = f"{settings.API_BASE_URL}/media/selfies/{unique_filename}"
    updated_user = await crud_user.update_user(
        db, user=current_user, data_to_update={"selfie": public_url}
    )

    return updated_user