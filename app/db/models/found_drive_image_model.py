# app/db/models/found_drive_image_model.py

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class FoundDriveImage(Base):
    __tablename__ = "found_drive_images"

    id = Column(Integer, primary_key=True, index=True)
    id_drive_search = Column(Integer, ForeignKey("drive_searches.id"), nullable=False)
    
    original_drive_id = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    url = Column(Text, unique=True, nullable=False)
    
    face_coords = Column(JSONB)
    similarity = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relasi: Satu gambar yang ditemukan milik satu sesi pencarian
    search_session = relationship("DriveSearch", back_populates="found_images")