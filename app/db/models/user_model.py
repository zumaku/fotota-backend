# app/db/models/user_model.py

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    # KEMBALI MENGGUNAKAN INTEGER AUTO-INCREMENT SEBAGAI PRIMARY KEY
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    picture = Column(Text, nullable=True)
    selfie = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # google_id sekarang menjadi kolom biasa yang unik, bukan primary key
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    
    google_refresh_token = Column(Text, nullable=True)
    internal_refresh_token_hash = Column(String(255), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relasi tidak berubah, tapi foreign key di tabel lain akan merujuk ke Integer
    events = relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    saved_photos = relationship("Fotota", back_populates="user", cascade="all, delete-orphan")