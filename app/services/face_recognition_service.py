# app/services/face_recognition_service.py

import os
import time
import asyncio
import logging
from typing import List, Dict, Any
from deepface import DeepFace
from fastapi.concurrency import run_in_threadpool
from app.crud import crud_event
from app.core.config import settings
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

def convert_public_url_to_local_path(url: str) -> str:
    """Mengubah URL publik kembali menjadi path disk lokal."""
    # Contoh: http://localhost:8000/media/selfies/file.jpg -> storage/selfies/file.jpg
    # Kita asumsikan BACKEND_ROOT sudah terdefinisi di settings
    base_url = settings.API_BASE_URL
    relative_path = url.replace(f"{base_url}/media/", "storage/", 1)
    # Ini masih path relatif dari folder backend, DeepFace bisa menanganinya
    return relative_path

async def find_matching_faces(
    source_image_url: str,
    event_storage_path: str # Path ke folder event, cth: storage/events/12
) -> List[Dict[str, Any]]:
    """
    Menjalankan DeepFace.find di thread terpisah untuk mencari wajah yang cocok.
    Mengembalikan daftar URL publik dari gambar yang cocok.
    """
    try:
        # Ubah URL selfie menjadi path lokal
        source_image_path = convert_public_url_to_local_path(source_image_url)

        # Jalankan DeepFace.find yang berat di thread terpisah
        # Ini adalah bagian terpenting untuk menjaga performa server
        # DeepFace.find mengembalikan pandas DataFrame
        dfs = await run_in_threadpool(
            DeepFace.find,
            img_path=source_image_path,
            db_path=event_storage_path,
            model_name=settings.MODEL_NAME,
            enforce_detection=False # Jangan error jika tidak ada wajah di gambar sumber
        )

        # DeepFace mengembalikan list of DataFrames
        if not isinstance(dfs, list) or len(dfs) == 0:
            return []

        # Ambil DataFrame pertama yang berisi hasil
        result_df = dfs[0]

        # Filter hasil untuk mendapatkan path file yang cocok
        # 'identity' adalah path ke file yang ditemukan di db_path
        # Jika tidak ada kolom 'identity' atau kosong, kembalikan list kosong
        if "identity" not in result_df.columns or result_df.empty:
            return []
        
        # Ekstrak data lengkap dari DataFrame
        results = []
        for index, row in result_df.iterrows():
            # 'identity' adalah path disk ke gambar yang cocok
            # 'target_x', 'target_y', 'target_w', 'target_h' adalah koordinatnya
            results.append({
                "disk_path": row["identity"].replace("\\", "/"), # Normalisasi path separator
                "face_coords": {
                    "x": row["target_x"],
                    "y": row["target_y"],
                    "w": row["target_w"],
                    "h": row["target_h"],
                }
            })
        
        return results

    except Exception as e:
        # Tangani error jika DeepFace gagal atau folder tidak ada
        print(f"DeepFace Error: {e}")
        return []

def _blocking_deepface_call(source_path: str, db_path: str):
    """
    Fungsi pembungkus sinkron untuk panggilan DeepFace yang berat.
    Fungsi 'pekerja' sinkron ini akan berjalan di background.
    Tugasnya adalah memindai folder event untuk membuat file cache .pkl.
    """
    logger.info(f"DeepFace analysis started for folder: {db_path}")
    DeepFace.find(
        img_path=source_path,
        db_path=db_path,
        model_name=settings.MODEL_NAME,
        enforce_detection=False
    )
    logger.info(f"DeepFace analysis finished for folder: {db_path}")

async def process_event_images_and_update_status(event_id: int, event_storage_path: str):
    """
    Fungsi 'pekerja' asinkron yang lengkap. Ini akan dipanggil sebagai background task.
    Ia membuat sesi DB sendiri, menjalankan AI, dan mengupdate status.
    """
    logger.info(f"BACKGROUND TASK: Starting for event_id: {event_id}")
    
    # Langkah 1: Buat Sesi Database (Nampan) baru khusus untuk tugas ini
    db = AsyncSessionLocal()
    
    try:
        # Beri jeda untuk sinkronisasi file sistem
        await asyncio.sleep(2)

        images_in_folder = [f for f in os.listdir(event_storage_path) if f.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'))]
        if not images_in_folder:
            logger.warning(f"BACKGROUND TASK: No images found for event {event_id}. Task skipped.")
            return

        # Ambil satu gambar sebagai pemicu
        trigger_image_path = os.path.join(event_storage_path, images_in_folder[0])

        # Langkah 2: Jalankan tugas berat (AI) di thread terpisah
        await run_in_threadpool(_blocking_deepface_call, trigger_image_path, event_storage_path)
        
        # Langkah 3: Gunakan Sesi DB untuk mengupdate status menjadi True
        await crud_event.set_event_indexed_status(db=db, event_id=event_id, status=True)
        
        logger.info(f"BACKGROUND TASK: Successfully indexed event {event_id} and updated status in DB.")

    except Exception as e:
        logger.error(f"BACKGROUND TASK FAILED for event {event_id}. Error: {e}", exc_info=True)
    finally:
        # Langkah 4: Sangat penting untuk selalu menutup sesi database
        await db.close()
        logger.info(f"BACKGROUND TASK: DB session closed for event {event_id}.")