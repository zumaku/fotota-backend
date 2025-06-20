# app/services/drive_service.py

import logging
import io
import cv2
import uuid
import os
import numpy as np
from typing import List, Dict, Any
from fastapi.concurrency import run_in_threadpool
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.core.config import settings
from app.core.model_loader import face_app
from app.db.database import AsyncSessionLocal
from app.crud import crud_drive_search
from .face_recognition_service import convert_public_url_to_local_path

def _blocking_drive_search(folder_id: str, selfie_embedding: np.ndarray) -> List[Dict[str, Any]]:
    """Fungsi sinkron yang berisi logika inti dari pencarian gambar di shared drive."""
    
    # 1. Inisialisasi Google Drive service
    drive_service = build('drive', 'v3', developerKey=settings.GOOGLE_API_KEY)
    
    # 2. Ambil daftar file dari folder
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = drive_service.files().list(q=query, pageSize=100, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if not items:
        print(f"No images found in Google Drive folder: {folder_id}")
        return []

    matched_images = []
    
    # 3. Loop, download, dan proses setiap gambar
    for item in items:
        file_id = item.get('id')
        file_name = item.get('name')
        print(f"Processing file: {file_name} (ID: {file_id})")
        
        try:
            # Download file ke memori
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Ubah byte data menjadi gambar OpenCV
            fh.seek(0)
            image_bytes = np.frombuffer(fh.read(), np.uint8)
            img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

            if img is None: continue
            
            # Deteksi wajah di gambar dari Drive
            faces_in_image = face_app.app.get(img)

            # Bandingkan setiap wajah dengan embedding selfie
            for face in faces_in_image:
                similarity = np.dot(selfie_embedding, face.normed_embedding)
                if similarity > 0.5: # Threshold kemiripan
                    bbox = face.bbox
                    matched_images.append({
                        "original_drive_id": file_id,
                        "original_file_name": file_name,
                        "face_coords": {"x": int(bbox[0]), "y": int(bbox[1]), "w": int(bbox[2]-bbox[0]), "h": int(bbox[3]-bbox[1])},
                        "similarity": float(similarity),
                        "image_bytes": cv2.imencode('.jpg', img)[1].tobytes() # Simpan gambar sebagai bytes
                    })
                    print(f"✅ Match found in {file_name} with similarity {similarity:.2f}")
                    break # Lanjut ke gambar berikutnya setelah menemukan 1 wajah cocok
        except Exception as e:
            print(f"Failed to process file {file_name} from Drive. Error: {e}")
            continue
            
    return matched_images

async def run_drive_search_and_save(search_id: int, folder_id: str, user_selfie_url: str):
    """Fungsi pembungkus asinkron untuk dijalankan sebagai background task."""
    print(f"DRIVE SEARCH TASK: Starting for search_id: {search_id}")
    db = AsyncSessionLocal()
    try:
        # Dapatkan embedding dari selfie user
        selfie_path = convert_public_url_to_local_path(user_selfie_url)
        img_selfie = cv2.imread(selfie_path)
        faces = face_app.app.get(img_selfie)
        if not faces:
            raise ValueError("No face found in user's selfie.")
        selfie_embedding = faces[0].normed_embedding

        # Jalankan pencarian di thread terpisah
        matched_results = await run_in_threadpool(_blocking_drive_search, folder_id, selfie_embedding)
        
        # Simpan setiap hasil ke storage dan database
        for result in matched_results:
            unique_filename = f"{uuid.uuid4()}.jpg"
            file_path_on_disk = settings.STORAGE_ROOT_PATH / "drive-events" / str(search_id) / unique_filename
            os.makedirs(file_path_on_disk.parent, exist_ok=True)
            
            with open(file_path_on_disk, 'wb') as f:
                f.write(result["image_bytes"])
            
            public_url = f"{settings.API_BASE_URL}/media/drive-events/{search_id}/{unique_filename}"
            
            await crud_drive_search.add_found_image(
                db, 
                search_id=search_id, 
                image_data={
                    **result, # Menggabungkan face_coords, similarity, dll
                    "file_name": unique_filename,
                    "url": public_url
                }
            )
        
        # Update status pencarian menjadi 'completed'
        await crud_drive_search.update_drive_search_status(db, search_id=search_id, status="completed")
        print(f"✅ DRIVE SEARCH TASK: Finished for search_id: {search_id}. Found {len(matched_results)} matches.")

    except Exception as e:
        await crud_drive_search.update_drive_search_status(db, search_id=search_id, status="failed")
        print(f"❌ DRIVE SEARCH TASK FAILED for search_id: {search_id}. Error: {e}", exc_info=True)
    finally:
        await db.close()