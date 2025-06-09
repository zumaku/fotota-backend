# app/crud/crud_fotota.py

from typing import List, Optional
from sqlalchemy.orm import selectinload, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.models import Fotota as FototaModel, Image as ImageModel, Event as EventModel

async def get_bookmark(db: AsyncSession, *, user_id: int, image_id: int) -> Optional[FototaModel]:
    """Mengecek apakah sebuah bookmark sudah ada untuk user dan image tertentu."""
    result = await db.execute(
        select(FototaModel).filter_by(id_user=user_id, id_image=image_id)
    )
    return result.scalars().first()

async def create_bookmark(db: AsyncSession, *, user_id: int, image_id: int) -> FototaModel:
    """Membuat record bookmark baru."""
    db_bookmark = FototaModel(id_user=user_id, id_image=image_id)
    db.add(db_bookmark)
    await db.commit()
    await db.refresh(db_bookmark)
    return db_bookmark

async def get_bookmark_by_id(db: AsyncSession, bookmark_id: int) -> Optional[FototaModel]:
    """Mengambil satu bookmark berdasarkan ID-nya."""
    return await db.get(FototaModel, bookmark_id)

async def delete_bookmark(db: AsyncSession, bookmark_to_delete: FototaModel):
    """Menghapus record bookmark."""
    await db.delete(bookmark_to_delete)
    await db.commit()

async def get_all_bookmarked_by_user(db: AsyncSession, *, user_id: int) -> List[FototaModel]:
    """
    Mengambil semua data bookmark milik seorang user, diurutkan dari yang terbaru,
    dan menyertakan data gambar serta event terkait.
    """
    query = (
        select(FototaModel)
        .join(FototaModel.image)
        .options(
            # Muat data gambar dan data event dari gambar tersebut secara efisien
            contains_eager(FototaModel.image).selectinload(ImageModel.event)
        )
        .filter(FototaModel.id_user == user_id)
        .order_by(desc(FototaModel.created_at))
    )
    result = await db.execute(query)
    # .unique() untuk menghindari duplikasi jika ada join yang kompleks
    return result.scalars().unique().all()