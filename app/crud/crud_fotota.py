# app/crud/crud_fotota.py

from typing import List, Optional
from sqlalchemy.orm import selectinload, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, delete

from app.db.models import Fotota as FototaModel, Image as ImageModel, Event as EventModel

async def get_bookmark(db: AsyncSession, *, user_id: int, image_id: int) -> Optional[FototaModel]:
    """Mengecek apakah sebuah bookmark sudah ada untuk user dan image tertentu."""
    result = await db.execute(
        select(FototaModel).filter_by(id_user=user_id, id_image=image_id)
    )
    return result.scalars().first()

async def bulk_create_bookmarks(db: AsyncSession, *, user_id: int, image_ids: List[int]) -> List[FototaModel]:
    """Membuat beberapa record bookmark sekaligus."""
    
    # 1. Cek dulu mana saja gambar yang sudah di-bookmark oleh user ini untuk menghindari duplikasi
    existing_bookmarks_stmt = select(FototaModel.id_image).filter(
        and_(FototaModel.id_user == user_id, FototaModel.id_image.in_(image_ids))
    )
    result = await db.execute(existing_bookmarks_stmt)
    existing_image_ids = set(result.scalars().all())

    # 2. Buat daftar bookmark baru hanya untuk image_id yang belum ada
    new_bookmarks = [
        FototaModel(id_user=user_id, id_image=image_id)
        for image_id in image_ids
        if image_id not in existing_image_ids
    ]

    if not new_bookmarks:
        return [] # Kembalikan list kosong jika tidak ada yang baru ditambahkan

    # 3. Simpan semua bookmark baru ke database dalam satu kali operasi
    db.add_all(new_bookmarks)
    await db.commit()
    
    # Refresh setiap objek baru untuk mendapatkan ID dan data relasi
    for bm in new_bookmarks:
        await db.refresh(bm)
        
    return new_bookmarks

async def get_bookmark_by_id(db: AsyncSession, bookmark_id: int) -> Optional[FototaModel]:
    """Mengambil satu bookmark berdasarkan ID-nya."""
    return await db.get(FototaModel, bookmark_id)

async def bulk_delete_bookmarks_by_ids(db: AsyncSession, *, user_id: int, bookmark_ids: List[int]) -> int:
    """Menghapus beberapa bookmark berdasarkan daftar ID, hanya milik user yang bersangkutan."""
    
    # Query untuk menghapus record yang ID-nya ada di dalam daftar DAN dimiliki oleh user saat ini
    query = (
        delete(FototaModel)
        .where(
            and_(
                FototaModel.id.in_(bookmark_ids),
                FototaModel.id_user == user_id
            )
        )
    )
    result = await db.execute(query)
    await db.commit()
    
    # result.rowcount akan berisi jumlah baris yang berhasil dihapus
    return result.rowcount

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