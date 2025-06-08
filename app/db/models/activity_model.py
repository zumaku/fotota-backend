# app/db/models/activity_model.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # DIUBAH: Foreign Key ke events.id sekarang adalah Integer
    id_event = Column(Integer, ForeignKey("events.id"), nullable=False)
    # DIUBAH: Foreign Key ke users.id sekarang adalah Integer
    id_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event = relationship("Event", back_populates="activities")
    user = relationship("User", back_populates="activities")