# app/schemas/image_schema.py
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