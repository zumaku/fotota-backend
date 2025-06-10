# app/services/face_recognition_service.py

import os
import time
import logging
from typing import List, Dict, Any
from deepface import DeepFace
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)

def pre_calculate_event_embeddings(event_storage_path: str):
    """
    Fungsi 'pekerja' sinkron yang akan berjalan di background.
    Tugasnya adalah memindai folder event untuk membuat file cache .pkl.
    """
    try:
        # Beri jeda 2 detik untuk memastikan semua file sudah selesai ditulis ke disk oleh OS.
        logger.info(f"BACKGROUND TASK: Waiting 2 seconds for file system to sync for event path: {event_storage_path}")
        time.sleep(2)
        
        # Kita perlu setidaknya satu gambar di dalam folder untuk dijadikan 'img_path'
        # Kita bisa ambil gambar pertama secara acak.
        images_in_folder = [f for f in os.listdir(event_storage_path) if f.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'))]
        if not images_in_folder:
            logger.error(f"BACKGROUND TASK: No images in {event_storage_path} to build index from.", exc_info=True)
            return

        # Ambil satu gambar sebagai pemicu
        trigger_image_path = os.path.join(event_storage_path, images_in_folder[0])

        logger.info(f"BACKGROUND TASK: Starting to build face database for {event_storage_path}...")
        
        # Panggilan ini akan secara otomatis membuat atau memperbarui file .pkl
        # Kita tidak perlu menyimpan hasilnya, kita hanya butuh prosesnya berjalan.
        _ = DeepFace.find(
            img_path=trigger_image_path,
            db_path=event_storage_path,
            model_name="Facenet512",
            enforce_detection=False
        )
        
        logger.info(f"BACKGROUND TASK: Face database for {event_storage_path} is ready.")

    except Exception as e:
        # Penting untuk mencatat error jika terjadi di background
        logger.error(f"BACKGROUND TASK FAILED for {event_storage_path}. Error: {e}", exc_info=True)

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