# app/db/models/face_model.py

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector # <-- Impor tipe Vector
from app.db.base_class import Base
from app.core.config import settings

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    id_image = Column(Integer, ForeignKey("images.id"), nullable=False)
    
    # Definisikan dimensi vektor agar cocok dengan database
    embedding = Column(Vector(settings.DEEPFACE_VECTOR_DIMENSION))
    
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    w = Column(Integer, nullable=False)
    h = Column(Integer, nullable=False)

    # Relasi kembali ke gambar induknya
    image = relationship("Image", back_populates="faces")