# app/crud/crud_event.py

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.event_model import Event as EventModel
from app.schemas.event_schema import EventCreate, EventUpdate
from app.core.security import get_password_hash, verify_password

async def create_event(db: AsyncSession, *, event_in: EventCreate, owner_id: int) -> EventModel:
    hashed_password = get_password_hash(event_in.password)
    # Buat instance model DB dengan data dari skema Pydantic
    db_event = EventModel(
        name=event_in.name,
        description=event_in.description,
        date=event_in.date,
        hashed_password=hashed_password,
        id_user=owner_id
    )
    db.add(db_event)
    try:
        await db.commit()
        await db.refresh(db_event)
        return db_event
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error on event creation: {e}")

async def get_events_by_owner(db: AsyncSession, *, owner_id: int) -> List[EventModel]:
    result = await db.execute(select(EventModel).filter(EventModel.id_user == owner_id).order_by(EventModel.date.desc()))
    return result.scalars().all()

async def get_event_by_id(db: AsyncSession, event_id: int) -> Optional[EventModel]:
    return await db.get(EventModel, event_id)

async def search_events_by_name(db: AsyncSession, *, query: str) -> List[EventModel]:
    """Mencari event berdasarkan nama secara case-insensitive."""
    search_query = f"%{query}%"
    result = await db.execute(select(EventModel).filter(EventModel.name.ilike(search_query)).order_by(EventModel.date.desc()))
    return result.scalars().all()

async def update_event(db: AsyncSession, *, event_db_obj: EventModel, event_in: EventUpdate) -> EventModel:
    """Mengupdate sebuah event."""
    update_data = event_in.model_dump(exclude_unset=True) # Hanya ambil field yang diisi
    
    # Jika password diupdate, hash password baru
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]

    for field, value in update_data.items():
        setattr(event_db_obj, field, value)
    
    db.add(event_db_obj)
    try:
        await db.commit()
        await db.refresh(event_db_obj)
        return event_db_obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error on event update: {e}")

async def delete_event(db: AsyncSession, event_to_delete: EventModel):
    await db.delete(event_to_delete)
    await db.commit()