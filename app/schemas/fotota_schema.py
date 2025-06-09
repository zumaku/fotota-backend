# app/schemas/fotota_schema.py

from typing import Optional
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# Impor skema ImagePublic yang akan kita gunakan di dalam respons
from .image_schema import ImagePublic

# Skema untuk request body saat membuat bookmark baru
class FototaCreate(BaseModel):
    image_id: int = Field(..., description="ID dari gambar yang ingin di-bookmark")

# Skema untuk menampilkan satu record bookmark (termasuk detail gambarnya)
class FototaPublic(BaseModel):
    id: int
    created_at: datetime
    image: ImagePublic # <-- Kita sisipkan detail gambar di sini

    class Config:
        from_attributes = True

# Skema khusus untuk respons endpoint "get my bookmarks" yang dikelompokkan per event
class BookmarkedEventGroup(BaseModel):
    event_id: int
    event_name: str
    event_date: Optional[datetime]
    bookmarked_photos: List[FototaPublic] # <-- Daftar foto yang di-bookmark untuk event ini