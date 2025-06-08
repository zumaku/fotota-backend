# app/schemas/event_schema.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Properti dasar untuk membuat atau menampilkan event
class EventBase(BaseModel):
    name: str = Field(..., min_length=3, example="Pernikahan Budi & Ani")
    description: Optional[str] = Field(None, example="Wedding party of Budi and Ani.")
    date: Optional[datetime] = Field(None, example="2025-12-25T10:00:00Z")

# Skema untuk membuat event baru, password wajib diisi
class EventCreate(EventBase):
    password: str = Field(..., min_length=4, example="BudiAni2025")

# Skema untuk mengupdate event, semua field opsional
class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = None
    date: Optional[datetime] = None
    password: Optional[str] = Field(None, min_length=4) # Admin bisa ganti password

# Skema yang dikembalikan ke client, tidak ada password
class EventPublic(EventBase):
    id: int
    link: Optional[str] = Field(None, example="https://fotota.app/event/unique-link-string")
    id_user: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True