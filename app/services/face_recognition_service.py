# app/services/face_recognition_service.py

import logging
import asyncio
from typing import List, Dict, Any
from deepface import DeepFace
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import settings
from app.crud import crud_face, crud_event
from app.db.database import AsyncSessionLocal
from app.db.models import Face as FaceModel, Image as ImageModel

logger = logging.getLogger(__name__)

def _blocking_represent_one_image(image_path: str) -> List[Dict[str, Any]]:
    """Fungsi pembungkus sinkron yang hanya memproses SATU gambar."""
    try:
        extracted_faces = DeepFace.represent(
            img_path=image_path,
            model_name=settings.DEEPFACE_MODEL_NAME,
            # enforce_detection=True,
        )
        # face_data_list = []
        # for face in extracted_faces:
        #     coords = face.facial_area
        #     face_data_list.append({
        #         "embedding": face.embedding,
        #         "x": coords.x,
        #         "y": coords.y,
        #         "w": coords.w,
        #         "h": coords.h,
        #     })
        # return face_data_list
        return extracted_faces
    except Exception:
        return []

async def process_image_batch_and_save_faces(image_jobs: List[Dict[str, Any]]):
    """
    Fungsi pembungkus asinkron untuk dijalankan sebagai background task.
    Menerima daftar pekerjaan dan memprosesnya satu per satu.
    """
    logger.info(f"BACKGROUND TASK: Starting to process a batch of {len(image_jobs)} images.")
    db = AsyncSessionLocal()
    try:
        # Loop melalui setiap pekerjaan (gambar) secara berurutan
        for job in image_jobs:
            image_id = job["image_id"]
            image_path = job["image_path"]

            # Jalankan proses AI yang berat di thread terpisah
            extracted_faces = await run_in_threadpool(_blocking_represent_one_image, image_path)
            
            if not extracted_faces:
                logger.warning(f"No faces found in image_id: {image_id}. Skipping.")
                continue

            # Simpan setiap wajah yang ditemukan ke database
            for face_data in extracted_faces:
                face_data['id_image'] = image_id
                await crud_face.create_face_embedding(db, face_data=face_data)
            
            logger.info(f"✅ Processed image_id: {image_id}, found {len(extracted_faces)} faces.")
        
        # Setelah semua selesai, kita bisa update status event
        if image_jobs:
            event_id = image_jobs[0].get("event_id")
            if event_id:
                await crud_event.set_event_indexed_status(db, event_id=event_id, status=True)
                logger.info(f"✅ BACKGROUND TASK: Finished processing batch and marked event {event_id} as indexed.")

    except Exception as e:
        logger.error(f"❌ BACKGROUND TASK FAILED during batch processing. Error: {e}", exc_info=True)
    finally:
        await db.close()

async def find_similar_faces_in_db(
    db: AsyncSession, *, event_id: int, target_embedding: List[float], threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Mencari wajah yang mirip di database menggunakan perbandingan vektor.
    """
    # Query untuk mencari wajah di event tertentu yang jaraknya di bawah threshold
    # <=> adalah operator Cosine Distance dari pgvector
    query = (
        select(FaceModel, FaceModel.embedding.cosine_distance(target_embedding).label("distance"))
        .join(ImageModel)
        .filter(ImageModel.id_event == event_id)
        .filter(FaceModel.embedding.cosine_distance(target_embedding) < threshold)
        .order_by(FaceModel.embedding.cosine_distance(target_embedding))
    )
    
    result = await db.execute(query)
    
    # Proses hasil untuk digabungkan menjadi respons
    final_matches = []
    # Gunakan dict untuk memastikan kita hanya mengembalikan satu gambar sekali, meskipun ada banyak wajah cocok di dalamnya
    image_matches = {}

    for face, distance in result.all():
        if face.id_image not in image_matches:
            # Muat relasi image secara async
            image = await db.get(ImageModel, face.id_image)
            image_matches[face.id_image] = {
                "image_obj": image,
                "faces": []
            }
        
        image_matches[face.id_image]["faces"].append({
            "x": face.x, "y": face.y, "w": face.w, "h": face.h
        })

    # Ubah format menjadi list of dictionaries
    for img_id, data in image_matches.items():
        img = data["image_obj"]
        final_matches.append({
            "id": img.id,
            "file_name": img.file_name,
            "url": img.url,
            "id_event": img.id_event,
            "created_at": img.created_at,
            "face": data["faces"][0] # Ambil koordinat wajah pertama yang cocok sebagai representasi
        })

    return final_matches