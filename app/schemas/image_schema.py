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