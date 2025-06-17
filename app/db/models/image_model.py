# app/db/models/image_model.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    url = Column(Text, unique=True, nullable=False)
    
    # DIUBAH: Foreign Key ke events.id sekarang adalah Integer
    id_event = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event = relationship("Event", back_populates="images")
    faces = relationship("Face", back_populates="image", cascade="all, delete-orphan")
    saved_by_users = relationship("Fotota", back_populates="image", cascade="all, delete-orphan")