# app/api/routers/image_router.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.config import settings
from app.db.models import User as UserModel, Image as ImageModel
from app.crud import crud_image

router = APIRouter()

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an Image")
async def delete_an_image(
    image_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Menghapus sebuah gambar dari event dan dari storage.
    Hanya bisa dilakukan oleh admin pemilik event dari gambar tersebut.
    """
    # Kita tetap pakai eager loading untuk verifikasi kepemilikan
    image = await crud_image.get_image_with_event(db=db, image_id=image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    
    if image.event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this event's images.")
        
    # Hapus file dari disk
    relative_path = image.url.replace(f"{settings.API_BASE_URL}/", "").replace("media/", "storage/", 1)
    if os.path.exists(relative_path):
        os.remove(relative_path)
    
    # Hapus record dari database
    await db.delete(image)
    await db.commit()
    
    return None