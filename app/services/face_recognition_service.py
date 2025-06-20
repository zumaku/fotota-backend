# app/services/face_recognition_service.py

import logging
import cv2
import os
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool

from app.core.model_loader import face_app # Model yang sudah di-load saat startup
from app.core.config import settings

logger = logging.getLogger(__name__)

def convert_public_url_to_local_path(url: str) -> Optional[str]:
    """Mengubah URL publik kembali menjadi path disk lokal yang absolut."""
    if not url or not url.startswith(settings.API_BASE_URL):
        return None
    relative_path_from_media = url.replace(f"{settings.API_BASE_URL}/media/", "", 1)
    return str(settings.STORAGE_ROOT_PATH / relative_path_from_media)

async def find_similar_faces_in_folder_blocking(
    target_embedding: np.ndarray, 
    event_storage_path: str,
    threshold: float = 0.5 # Ambang batas Cosine Similarity
) -> List[Dict[str, Any]]:
    """
    Fungsi yang melakukan pekerjaan berat:
    Memindai folder, mengekstrak wajah, dan membandingkan embedding.
    """
    
    def _blocking_search():
        matched_results = []
        image_files = [f for f in os.listdir(event_storage_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        for filename in image_files:
            file_path = os.path.join(event_storage_path, filename)
            
            try:
                img = cv2.imread(file_path)
                if img is None:
                    continue

                # Deteksi semua wajah di gambar saat ini
                faces_in_image = face_app.app.get(img)

                for face in faces_in_image:
                    # Hitung cosine similarity (dot product dari embedding ternormalisasi)
                    similarity = np.dot(target_embedding, face.normed_embedding)
                    
                    if similarity > threshold:
                        bbox = face.bbox
                        matched_results.append({
                            "disk_path": file_path.replace("\\", "/"),
                            "face_coords": {
                                "x": int(bbox[0]),
                                "y": int(bbox[1]),
                                "w": int(bbox[2] - bbox[0]),
                                "h": int(bbox[3] - bbox[1]),
                            },
                            "similarity": similarity # Kirim juga skor kemiripan
                        })
                        # Kita hanya ambil satu wajah yang paling cocok per gambar
                        break 
            except Exception as e:
                logger.warning(f"Could not process image {filename}: {e}")
                continue

        # Urutkan hasil berdasarkan kemiripan tertinggi
        matched_results.sort(key=lambda x: x['similarity'], reverse=True)
        return matched_results

    # Jalankan fungsi blocking di thread terpisah
    return await run_in_threadpool(_blocking_search)