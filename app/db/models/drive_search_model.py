# app/db/models/drive_search_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class DriveSearch(Base):
    __tablename__ = "drive_searches"

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    drive_folder_id = Column(String(255), nullable=False)
    status = Column(String(50), default="processing", nullable=False) # processing, completed, failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relasi ke user yang memulai pencarian
    owner = relationship("User", back_populates="drive_searches")

    # Relasi ke gambar-gambar yang ditemukan dari pencarian ini
    found_images = relationship("FoundDriveImage", back_populates="search_session", cascade="all, delete-orphan")


class FoundDriveImage(Base):
    __tablename__ = "found_drive_images"

    id = Column(Integer, primary_key=True)
    id_drive_search = Column(Integer, ForeignKey("drive_searches.id"), nullable=False, index=True)
    original_drive_id = Column(String(255), nullable=True) # ID file asli di Google Drive

    file_name = Column(String(255), nullable=False) # Nama file unik di storage kita
    url = Column(String(255), unique=True, nullable=False) # URL publik di server kita

    face_coords = Column(JSON, nullable=True) # Menyimpan x, y, w, h
    similarity = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi kembali ke sesi pencarian
    search_session = relationship("DriveSearch", back_populates="found_images")