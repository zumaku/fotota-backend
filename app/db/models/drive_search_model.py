# app/db/models/drive_search_model.py

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DriveSearch(Base):
    __tablename__ = "drive_searches"

    id = Column(Integer, primary_key=True, index=True)
    drive_folder_id = Column(String(255), nullable=False)
    drive_url = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="processing")
    
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relasi: Satu sesi pencarian dimiliki oleh satu user
    owner = relationship("User")
    
    # Relasi: Satu sesi pencarian bisa menghasilkan banyak gambar yang ditemukan
    found_images = relationship("FoundDriveImage", back_populates="search_session", cascade="all, delete-orphan")