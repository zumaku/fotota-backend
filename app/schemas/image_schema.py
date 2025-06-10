# app/schemas/image_schema.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class ImagePublic(BaseModel):
    id: int
    file_name: str
    url: str
    id_event: int
    created_at: datetime

    class Config:
        from_attributes = True

# Enum untuk validasi parameter sorting
class ImageSortBy(str, Enum):
    created_at = "created_at"
    file_name = "file_name"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"
    
class FaceCoordinates(BaseModel):
    """Skema untuk menyimpan koordinat kotak pembatas wajah."""
    x: int
    y: int
    w: int # width
    h: int # height

class MatchedImageResult(ImagePublic):
    """
    Skema yang dikembalikan saat pencarian wajah berhasil.
    Mewarisi semua field dari ImagePublic dan menambahkan data koordinat wajah.
    """
    face: FaceCoordinates # <-- Objek bersarang berisi data x, y, w, h