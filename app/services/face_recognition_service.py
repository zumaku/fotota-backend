# app/services/face_recognition_service.py

import pandas as pd
from typing import List
from deepface import DeepFace
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

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
) -> List[str]:
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
            model_name="Dlib",
            enforce_detection=False # Jangan error jika tidak ada wajah di gambar sumber
        )

        # DeepFace mengembalikan list of DataFrames
        if not isinstance(dfs, list) or len(dfs) == 0:
            return []

        # Ambil DataFrame pertama yang berisi hasil
        result_df = dfs[0]

        # Filter hasil untuk mendapatkan path file yang cocok
        # 'identity' adalah path ke file yang ditemukan di db_path
        matched_file_paths = result_df["identity"].tolist()

        # Ubah kembali path disk lokal menjadi URL publik
        # cth: storage/events/12/foto.jpg -> http://.../media/events/12/foto.jpg
        matched_urls = [
            path.replace("storage/", f"{settings.API_BASE_URL}/media/", 1).replace("\\", "/")
            for path in matched_file_paths
        ]
        
        return matched_urls

    except Exception as e:
        # Tangani error jika DeepFace gagal atau folder tidak ada
        print(f"DeepFace Error: {e}")
        return []