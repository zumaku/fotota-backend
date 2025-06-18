# app/schemas/event_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user_schema import UserInfo
from .image_schema import MatchedImageResult

# Properti dasar untuk membuat atau menampilkan event
class EventBase(BaseModel):
    name: str = Field(..., min_length=3, example="Presentasi Karya Inready Workgroup 2024")
    description: Optional[str] = Field(None, example="Pameran karya dari angkatan muda Inready Workgroup.")
    date: Optional[datetime] = Field(None, example="2024-12-25T10:00:00Z")

# Skema untuk membuat event baru, password wajib diisi
class EventCreate(EventBase):
    password: str = Field(..., min_length=4, example="hitamEmas")

# Skema untuk mengupdate event, semua field opsional
class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = None
    date: Optional[datetime] = None
    password: Optional[str] = Field(None, min_length=4) # Admin bisa ganti password
    link: Optional[str]
    share_code: Optional[str]

# Skema baru untuk password event
class EventAccessRequest(BaseModel):
    password: str = Field(..., example="PasswordEventRahasia")
    
# SKEMA BARU UNTUK RESPONS TOKEN EVENT
class EventAccessToken(BaseModel):
    event_access_token: str
    token_type: str = "bearer"
    

# ----------------------------------

class EventInDBBase(EventBase):
    id: int
    link: Optional[str]
    share_code: Optional[str]
    indexed_by_robota: bool
    created_at: datetime
    updated_at: datetime
    images_preview: List[str] = [] # Field baru untuk preview gambar

    class Config:
        from_attributes = True

# Skema yang dikembalikan ke client, tidak ada password
class EventPublicDetail(EventInDBBase):
    """
    Tampilan detail sebuah event.
    Mengembalikan objek 'owner' yang berisi info user.
    """
    owner: UserInfo # <-- Field baru berisi objek info user

class EventPublicSummary(EventInDBBase):
    """
    Tampilan ringkas untuk daftar event.
    Hanya mengembalikan 'id_user'.
    """
    id_user: int # <-- Hanya ID user, bukan objek lengkap

# ----------------------------------

class FaceSearchResponse(BaseModel):
    matched_images: List[MatchedImageResult]