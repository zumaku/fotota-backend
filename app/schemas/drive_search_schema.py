# app/schemas/drive_search_schema.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

# Impor skema koordinat wajah yang sudah kita buat
from .image_schema import FaceCoordinates

# Skema untuk body request saat memulai pencarian
class DriveSearchRequest(BaseModel):
    drive_url: HttpUrl # Pydantic akan otomatis memvalidasi ini sebagai URL yang valid

# Skema untuk respons awal setelah pencarian dimulai
class DriveSearchCreateResponse(BaseModel):
    search_id: int
    status: str
    message: str

# Skema untuk menampilkan satu gambar yang ditemukan
class FoundDriveImagePublic(BaseModel):
    id: int
    url: str
    face_coords: Optional[FaceCoordinates] = None
    similarity: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Skema untuk menampilkan satu item dalam daftar riwayat pencarian
class DriveSearchHistoryItem(BaseModel):
    search_id: int = Field(..., alias="id") # Ambil nilai dari atribut 'id'
    status: str
    drive_folder_id: str
    drive_name: str = None
    drive_url: Optional[HttpUrl] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Skema untuk respons akhir saat mengambil hasil pencarian
class DriveSearchResultResponse(BaseModel):
    search_id: int = Field(..., alias="id") # Ambil nilai dari atribut 'id'
    status: str
    drive_folder_id: str
    drive_name: str = None
    drive_url: Optional[HttpUrl] = None
    created_at: datetime
    found_images: List[FoundDriveImagePublic] = []