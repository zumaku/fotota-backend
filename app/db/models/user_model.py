from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import declarative_base # Atau from app.db.base_class import Base jika menggunakan base_class.py

# Jika tidak menggunakan base_class.py:
Base = declarative_base()

class User(Base): # Jika pakai base_class.py, ini jadi class User(Base): __tablename__ = "users"
    __tablename__ = "users" # Hapus ini jika __tablename__ otomatis dari Base

    # Jika tidak pakai id dari Base, definisikan di sini:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    picture = Column(Text, nullable=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # Simpan refresh token Google jika Anda perlu akses API Google di masa mendatang atas nama pengguna
    # Ini adalah refresh token DARI GOOGLE, BUKAN refresh token internal aplikasi Anda.
    google_refresh_token = Column(Text, nullable=True)
    
    # Simpan HASH dari refresh token INTERNAL aplikasi untuk keamanan dan pencabutan
    internal_refresh_token_hash = Column(String(255), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Jika Anda juga mendukung login password (tidak dibahas di sini tapi untuk skalabilitas)
    # hashed_password = Column(String(255), nullable=True)