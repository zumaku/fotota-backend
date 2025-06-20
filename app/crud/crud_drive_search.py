# app/crud/crud_drive_search.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from app.db.models import DriveSearch, FoundDriveImage
from app.schemas.drive_search_schema import FoundDriveImagePublic

async def create_drive_search(db: AsyncSession, *, user_id: int, folder_id: str) -> DriveSearch:
    """Membuat record baru saat pencarian dimulai."""
    db_search = DriveSearch(id_user=user_id, drive_folder_id=folder_id, status="processing")
    db.add(db_search)
    await db.commit()
    await db.refresh(db_search)
    return db_search

async def get_drive_search_results(db: AsyncSession, search_id: int) -> DriveSearch:
    """Mengambil hasil pencarian berdasarkan ID-nya."""
    result = await db.execute(
        select(DriveSearch)
        .options(selectinload(DriveSearch.found_images)) # Eager load gambar yang ditemukan
        .filter(DriveSearch.id == search_id)
    )
    return result.scalars().first()

async def add_found_image(db: AsyncSession, *, search_id: int, image_data: dict) -> FoundDriveImage:
    """Menyimpan satu gambar yang cocok ke database."""
    db_found_image = FoundDriveImage(
        id_drive_search=search_id,
        original_drive_id=image_data["original_drive_id"],
        file_name=image_data["file_name"],
        url=image_data["url"],
        face_coords=image_data["face_coords"],
        similarity=image_data["similarity"]
    )
    db.add(db_found_image)
    await db.commit()
    await db.refresh(db_found_image)
    return db_found_image

async def update_drive_search_status(db: AsyncSession, search_id: int, status: str):
    """Mengubah status sebuah sesi pencarian."""
    db_search = await db.get(DriveSearch, search_id)
    if db_search:
        db_search.status = status
        await db.commit()