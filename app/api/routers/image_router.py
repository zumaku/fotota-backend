# app/api/routers/image_router.py

import os
import uuid
import shutil
import aiofiles
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form

from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import crud_event, crud_image
from app.db.models import User as UserModel, Image as ImageModel
from app.schemas import image_schema
from app.core.config import settings

router = APIRouter()

# Path storage event yang sama dengan yang ada di event_router
EVENT_STORAGE_PATH = "storage/events"

@router.post("/upload", response_model=List[image_schema.ImagePublic], status_code=status.HTTP_201_CREATED, summary="Upload Images to an Event")
async def upload_images_to_event(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    # Karena kita mencampur File dan data lain, kita gunakan Form()
    event_id: int = Form(...),
    files: List[UploadFile] = File(...),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Mengunggah satu atau lebih foto ke sebuah event spesifik.
    Hanya admin yang memiliki event tersebut yang bisa mengunggah.
    """
    event = await crud_event.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    
    # Verifikasi kepemilikan event oleh admin yang sedang login
    if event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this event.")

    # Buat sub-direktori untuk event ini berdasarkan ID-nya
    event_photo_path = os.path.join(EVENT_STORAGE_PATH, str(event.id))
    os.makedirs(event_photo_path, exist_ok=True)
    
    created_images = []
    for file in files:
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            # Abaikan file yang bukan gambar atau lemparkan error
            continue

        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path_on_disk = os.path.join(event_photo_path, unique_filename)
        
        # Simpan file ke disk
        try:
            async with aiofiles.open(file_path_on_disk, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
        except Exception as e:
            # Jika gagal menyimpan satu file, mungkin kita ingin lanjut ke file berikutnya
            print(f"Could not save file {file.filename}. Error: {e}")
            continue

        # Buat URL publik yang akan digunakan oleh client
        # Path ini akan ditangani oleh StaticFiles di main.py
        public_url = f"{settings.API_BASE_URL}/media/events/{event.id}/{unique_filename}"
        
        # Simpan metadata gambar ke database
        db_image = await crud_image.create_event_image(
            db=db, file_name=unique_filename, url=public_url, event_id=event.id
        )
        created_images.append(db_image)

    if not created_images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid image files were uploaded.")

    return created_images

# Endpoint untuk menghapus gambar juga sebaiknya ada di sini
@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an Image")
async def delete_an_image(
    image_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Menghapus sebuah gambar dari event dan dari storage.
    Hanya bisa dilakukan oleh admin pemilik event.
    """
    
    # Menggunakan fungsi baru kita yang melakukan Eager Loading
    image = await crud_image.get_image_with_event(db=db, image_id=image_id)
    
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    
    # Verifikasi kepemilikan melalui event
    if image.event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this event's images.")
        
    # Hapus file dari disk
    # Kita perlu merekonstruksi path disk dari URL publiknya
    # Ini adalah contoh sederhana, mungkin perlu disesuaikan
    relative_path = image.url.replace("/media/", "storage/", 1)
    if os.path.exists(relative_path):
        os.remove(relative_path)
    
    # Hapus record dari database
    await db.delete(image)
    await db.commit()
    
    return None