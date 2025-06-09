# app/crud/crud_activity.py

from typing import List
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Activity as ActivityModel, Event as EventModel

async def get_recent_accessed_events_for_user(
    db: AsyncSession, *, user_id: int, limit: int = 5
) -> List[EventModel]:
    """
    Mengambil event yang paling baru diakses oleh seorang pengguna.
    Query ini sedikit kompleks:
    1. Mencari aktivitas unik per event berdasarkan waktu akses terakhir.
    2. Menggabungkannya dengan tabel event untuk mendapatkan detail.
    3. Mengurutkan berdasarkan waktu akses terakhir.
    """
    # Subquery untuk mendapatkan id_event unik dan waktu akses terakhirnya
    subquery = (
        select(
            ActivityModel.id_event,
            func.max(ActivityModel.updated_at).label("last_accessed_at")
        )
        .filter(ActivityModel.id_user == user_id)
        .group_by(ActivityModel.id_event)
        .subquery()
    )

    # Query utama untuk mengambil detail event berdasarkan hasil subquery
    query = (
        select(EventModel)
        .join(subquery, EventModel.id == subquery.c.id_event)
        .options(
            selectinload(EventModel.images) # Eager load images untuk preview
        )
        .order_by(desc(subquery.c.last_accessed_at))
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()

# Kita juga perlu fungsi untuk MEMBUAT record aktivitas, ini akan kita panggil nanti
async def log_user_activity(db: AsyncSession, *, user_id: int, event_id: int) -> ActivityModel:
    # Cek apakah sudah ada log untuk user dan event ini
    existing_activity_stmt = select(ActivityModel).filter_by(id_user=user_id, id_event=event_id)
    result = await db.execute(existing_activity_stmt)
    db_activity = result.scalars().first()
    
    if db_activity:
        # Jika sudah ada, kita hanya perbarui timestamp-nya
        # updated_at akan otomatis terupdate oleh 'onupdate=func.now()' di model
        # Namun, kita bisa set manual jika ingin lebih eksplisit
        pass # SQLAlchemy akan handle onupdate saat commit
    else:
        # Jika belum ada, buat record baru
        db_activity = ActivityModel(id_user=user_id, id_event=event_id)
        db.add(db_activity)
    
    await db.commit()
    await db.refresh(db_activity)
    return db_activity