# app/db/models/event_model.py

from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Event(Base):
    __tablename__ = "events"

    # Kita gunakan Integer agar konsisten, BigInt juga boleh jika event diperkirakan > 2 miliar
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String(255), unique=True, nullable=True)
    share_code = Column(String(16), unique=True, index=True, nullable=True)
    
    # DIUBAH: Foreign Key ke users.id sekarang adalah Integer
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    indexed_by_robota = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="events")
    images = relationship("Image", back_populates="event", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="event", cascade="all, delete-orphan")