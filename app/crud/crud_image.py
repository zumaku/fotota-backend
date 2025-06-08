# app/crud/crud_image.py

import math
from typing import Optional, Tuple, List
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.image_model import Image as ImageModel

async def create_event_image(db: AsyncSession, *, file_name: str, url: str, event_id: int) -> ImageModel:
    db_image = ImageModel(file_name=file_name, url=url, id_event=event_id)
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image

async def get_images_by_event_paginated(
    db: AsyncSession,
    *,
    event_id: int,
    page: int,
    limit: int,
    sort_by: str,
    sort_order: str,
    search: Optional[str]
) -> Tuple[List[ImageModel], int]:
    """
    Mengambil gambar dari event tertentu dengan pagination, sorting, dan search.
    Mengembalikan tuple berisi (daftar_gambar, jumlah_total_item).
    """
    # 1. Buat query dasar untuk memfilter berdasarkan event_id
    query = select(ImageModel).filter(ImageModel.id_event == event_id)

    # 2. Tambahkan filter pencarian jika ada
    if search:
        # Menggunakan ilike untuk pencarian case-insensitive
        query = query.filter(ImageModel.file_name.ilike(f"%{search}%"))

    # 3. Hitung jumlah total item SEBELUM pagination untuk metadata
    count_query = select(func.count()).select_from(query.subquery())
    total_items_result = await db.execute(count_query)
    total_items = total_items_result.scalar_one()

    # 4. Tentukan kolom untuk sorting
    sort_column = getattr(ImageModel, sort_by, ImageModel.created_at) # Default ke created_at jika field tidak valid

    # 5. Tentukan urutan sorting
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 6. Terapkan pagination (offset dan limit)
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # 7. Eksekusi query final untuk mendapatkan item halaman ini
    items_result = await db.execute(query)
    items = items_result.scalars().all()

    return items, total_items