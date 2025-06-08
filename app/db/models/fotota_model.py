# app/db/models/fotota_model.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Fotota(Base):
    __tablename__ = "fotota"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # DIUBAH: Foreign Key ke users.id sekarang adalah Integer
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    # DIUBAH: Foreign Key ke images.id sekarang adalah Integer
    id_image = Column(Integer, ForeignKey("images.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="saved_photos")
    image = relationship("Image", back_populates="saved_by_users")