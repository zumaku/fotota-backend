# app/crud/crud_face.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Face as FaceModel

async def create_face_embedding(db: AsyncSession, *, face_data: Dict[str, Any]) -> FaceModel:
    db_face = FaceModel(
        id_image=face_data["id_image"],
        embedding=face_data["embedding"],
        x=face_data["x"],
        y=face_data["y"],
        w=face_data["w"],
        h=face_data["h"],
    )
    db.add(db_face)
    await db.commit()
    await db.refresh(db_face)
    return db_face