# app/api/routers/event_router.py

import os
import uuid
import math
import shutil
import logging
import aiofiles
from deepface import DeepFace
from typing import Optional, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import crud_event, crud_image, crud_activity
from app.core import security
from app.core.config import settings
from app.db.models import User as UserModel, Event as EventModel
from app.schemas import event_schema, pagination_schema, image_schema, token_schema
from app.services import face_recognition_service

logger = logging.getLogger(__name__)

os.makedirs(settings.EVENT_STORAGE_PATH, exist_ok=True)

router = APIRouter()

# --- Helper Function untuk Logika Berulang ---
def get_image_previews(event: EventModel, limit: int = 4) -> List[str]:
    """Membuat daftar URL preview gambar dari sebuah event."""
    preview_urls = [image.url for image in event.images[:limit]]
    placeholder_url = f"{settings.API_BASE_URL}/media/events/no_image.png"
    while len(preview_urls) < limit:
        preview_urls.append(placeholder_url)
    return preview_urls

# --- Endpoint Definitions ---

@router.post("", response_model=event_schema.EventPublicDetail, status_code=status.HTTP_201_CREATED, summary="Create New Event")
async def create_event(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    event_in: event_schema.EventCreate,
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Membuat sebuah "folder" event baru. Hanya bisa diakses oleh admin.
    Upload foto dilakukan di endpoint terpisah.
    """
    
    # Buat event di database
    event = await crud_event.create_event(db=db, event_in=event_in, owner_id=admin_user.id)
    
    # Generate link unik setelah event dibuat dan memiliki ID
    unique_link = f"/events/{event.id}/{uuid.uuid4()}" # Contoh format link
    event_updated = await crud_event.update_event(db, event_db_obj=event, event_in=event_schema.EventUpdate(link=unique_link))
    
    # Langsung buat folder event di storage
    # event_folder_path = os.path.join(settings.EVENT_STORAGE_PATH, str(event_updated.id))
    event_folder_path = f"{settings.EVENT_STORAGE_PATH}/{event_updated.id}"
    os.makedirs(event_folder_path, exist_ok=True)
    logger.info(f"Created storage directory for event {event_updated.id} at {event_folder_path}")
    
    # Karena event baru belum punya gambar, kita buat preview placeholder secara manual
    placeholder_url = f"{settings.API_BASE_URL}/media/events/no_image.jpg"
    images_preview = [placeholder_url] * 4
    
    # Kita perlu memuat relasi 'owner' secara eksplisit untuk ditampilkan di respons.
    # Cara termudah adalah dengan memanggil kembali fungsi get_event_by_id yang sudah kita buat
    # karena fungsi itu sudah dikonfigurasi untuk melakukan eager loading.
    # Ini memastikan semua data yang dibutuhkan skema EventPublicDetail tersedia.
    final_event_obj = await crud_event.get_event_by_id(db, event_id=event.id)

    if not final_event_obj:
        # Ini seharusnya tidak pernah terjadi, tapi sebagai pengaman
        raise HTTPException(status_code=500, detail="Failed to fetch newly created event.")

    # Gabungkan semuanya menjadi respons Pydantic
    # Kita tidak bisa langsung 'return final_event_obj' karena kita perlu menyisipkan
    # images_preview yang kita buat secara manual.
    response_data = event_schema.EventPublicDetail.model_validate(final_event_obj, from_attributes=True)
    response_data.images_preview = images_preview

    return response_data

@router.get("/search", response_model=List[event_schema.EventPublicDetail], summary="Search for Events")
async def search_for_events(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    q: str = Query(..., min_length=3, description="Search query for event name"),
    # Endpoint ini bisa diakses semua user yang login, jadi kita pakai get_current_active_user
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mencari event berdasarkan nama.
    """
    events = await crud_event.search_events_by_name(db=db, query=q)
    for event in events:
        event.images_preview = get_image_previews(event)
    return events

@router.get("/my-events", response_model=List[event_schema.EventPublicDetail], summary="Get Events Created by Me")
async def get_my_created_events(
    db: AsyncSession = Depends(deps.get_db_session),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Mengambil daftar semua event yang telah dibuat oleh admin yang sedang login.
    """
    events = await crud_event.get_events_by_owner(db=db, owner_id=admin_user.id)
    for event in events:
        event.images_preview = get_image_previews(event)
    return events

@router.get("/{event_id}", response_model=event_schema.EventPublicDetail, summary="Get a Specific Event")
async def get_event_details(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mengambil detail sebuah event berdasarkan ID-nya.
    """
    event = await crud_event.get_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.images_preview = get_image_previews(event)
    return event

@router.put("/{event_id}", response_model=event_schema.EventPublicDetail, summary="Update an Event")
async def update_an_event(
    event_id: int,
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    event_in: event_schema.EventUpdate,
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Mengubah data sebuah event (nama, deskripsi, password, dll).
    Hanya bisa dilakukan oleh admin pemilik event.
    """
    event = await crud_event.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    updated_event = await crud_event.update_event(db=db, event_db_obj=event, event_in=event_in)
    updated_event.images_preview = get_image_previews(updated_event)
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an Event")
async def delete_an_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Menghapus sebuah event. Aksi ini akan menghapus event dan semua relasinya
    (termasuk foto di dalamnya, jika cascade di-setting dengan benar).
    Hanya bisa dilakukan oleh admin pemilik event.
    """
    
    # Verifikasi kepemilikan user
    event = await crud_event.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    # Tentukan path folder yang akan dihapus secara absolut
    event_folder_path = f"{settings.EVENT_STORAGE_PATH}/{event_id}"
    
    # Hapus folder dan isinya dari disk secara asinkron (di thread terpisah)
    if os.path.exists(event_folder_path):
        try:
            # shutil.rmtree adalah operasi blocking, jalankan di thread pool
            await run_in_threadpool(shutil.rmtree, event_folder_path)
            logger.info(f"Successfully deleted event folder: {event_folder_path}")
        except Exception as e:
            logger.error(f"Failed to delete event folder {event_folder_path}. Error: {e}", exc_info=True)
            # Jika gagal menghapus file, sebaiknya jangan lanjutkan ke penghapusan DB
            # agar data tetap konsisten dan bisa diperbaiki manual.
            raise HTTPException(status_code=500, detail="Failed to delete event assets from disk.")
            
    # 4. Jika file fisik berhasil dihapus (atau memang tidak ada), baru hapus record dari database
    await crud_event.delete_event(db=db, event_to_delete=event)

@router.post("/{event_id}/access", response_model=event_schema.EventAccessToken, summary="Get Event Access Token")
async def get_event_access_token(
    event_id: int,
    request_data: event_schema.EventAccessRequest,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Memverifikasi password event.
    Jika berhasil, kembalikan sebuah Event Access Token (EAT) yang berumur pendek.
    """
    event = await crud_event.get_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not security.verify_password(request_data.password, event.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    await crud_activity.log_user_activity(db=db, user_id=current_user.id, event_id=event.id)

    # Buat Event Access Token (EAT) yang berlaku 2 jam
    expires_delta = timedelta(hours=2)
    # Payload berisi klaim spesifik untuk akses event ini
    additional_claims = {"type": "event_access", "event_id": event.id}
    eat = security.create_jwt_token(
        subject=current_user.id,
        expires_delta=expires_delta,
        secret_key=settings.JWT_EVENT_SECRET_KEY,
        additional_claims=additional_claims
    )
    
    return event_schema.EventAccessToken(event_access_token=eat)

@router.get("/{event_id}/images", response_model=pagination_schema.PaginatedResponse[image_schema.ImagePublic], summary="Get Images in an Event with Pagination")
async def get_images_in_event(
    db: AsyncSession = Depends(deps.get_db_session),
    # Parameter query dengan validasi dan nilai default
    page: int = Query(1, gt=0, description="Halaman yang diminta"),
    limit: int = Query(10, gt=0, le=50, description="Jumlah item per halaman (max: 50)"),
    sort_by: image_schema.ImageSortBy = Query(image_schema.ImageSortBy.created_at, description="Field untuk sorting"),
    sort_order: image_schema.SortOrder = Query(image_schema.SortOrder.desc, description="Urutan sorting"),
    event_payload: token_schema.TokenPayload = Depends(deps.get_event_access_payload)
):
    """
    [ WAJIB menggunakan Event Access Token (EAT) yang didapat dari endpoint /access! ]
    
    Mengambil daftar gambar dari sebuah event dengan fitur lengkap:
    - **Pagination**: `page` dan `limit`
    - **Sorting**: `sort_by` (`created_at`, `file_name`) dan `sort_order` (`asc`, `desc`)
    - **Searching**: `search` (berdasarkan nama file)
    
    Endpoint ini bisa digunakan untuk mengimplementasikan "infinite scroll" di Flutter.
    """
    
    # Karena dependensi sudah memvalidasi, kita bisa langsung lanjut
    event_id = event_payload.event_id
    
    # Verifikasi dulu apakah event-nya ada
    event = await crud_event.get_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # TODO di masa depan: Tambahkan logika untuk memeriksa apakah user punya akses ke event ini (misal setelah memasukkan password)
    # DONE

    # Panggil fungsi CRUD yang canggih
    items, total_items = await crud_image.get_images_by_event_paginated(
        db=db,
        event_id=event_id,
        page=page, limit=limit, sort_by="created_at", sort_order="desc"
    )
    
    total_pages = math.ceil(total_items / limit)

    return pagination_schema.PaginatedResponse(
        total_items=total_items, total_pages=total_pages, current_page=page, limit=limit, items=items
    )
    
@router.post("/{event_id}/images", response_model=List[image_schema.ImagePublic], status_code=status.HTTP_201_CREATED, summary="Upload Images to a Specific Event")
async def upload_images_to_event(
    event_id: int,
    *,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db_session),
    files: List[UploadFile] = File(...),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    # ... (verifikasi event dan owner tetap sama) ...
    event = await crud_event.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.id_user != admin_user.id:
        raise HTTPException(status_code=403, detail="You do not own this event.")

    # Set status event kembali ke "sedang mengindeks"
    await crud_event.set_event_indexed_status(db, event_id=event_id, status=False)

    event_photo_path = f"{settings.EVENT_STORAGE_PATH}/{event.id}"
    logger.info(event_photo_path)
    os.makedirs(event_photo_path, exist_ok=True)
    
    # --- LOGIKA BARU: Kumpulkan semua pekerjaan dulu ---
    created_images = []
    image_processing_jobs = []

    for file in files:
        # ... (logika validasi dan penyimpanan file tetap sama) ...
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            continue

        unique_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        file_path_on_disk = f"{event_photo_path}/{unique_filename}"
        
        # Simpan file ke disk
        try:
            async with aiofiles.open(file_path_on_disk, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
        except Exception as e:
            logger.error(f"Failed to save uploaded file {file.filename}. Error: {e}")
            continue # Lanjut ke file berikutnya jika gagal menyimpan

        # Buat URL publik
        public_url = f"{settings.API_BASE_URL}/media/events/{event.id}/{unique_filename}"

        # Simpan metadata gambar ke DB
        db_image = await crud_image.create_event_image(
            db=db, file_name=unique_filename, url=public_url, event_id=event.id
        )
        created_images.append(db_image)

        # Tambahkan pekerjaan ke daftar
        image_processing_jobs.append({
            "event_id": event.id,
            "image_id": db_image.id,
            "image_path": file_path_on_disk
        })

    if not created_images:
        raise HTTPException(status_code=400, detail="No valid image files were uploaded.")

    # --- Panggil Background Task SATU KALI SAJA setelah loop selesai ---
    background_tasks.add_task(
        face_recognition_service.process_image_batch_and_save_faces,
        image_jobs=image_processing_jobs
    )
    
    logger.info(f"{len(created_images)} files uploaded. A batch processing task with {len(image_processing_jobs)} jobs has been scheduled for event {event_id}.")

    return created_images

@router.get("/{event_id}/find-my-face", response_model=List[image_schema.MatchedImageResult], summary="Find My Photos in an Event using Vector Search")
async def find_my_face_in_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Memulai proses pencarian wajah pengguna di semua foto dalam sebuah event
    menggunakan metode Vector Similarity Search di database.
    """
    # 1. Validasi Awal: Pastikan pengguna punya foto selfie
    if not current_user.selfie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must upload a selfie first before using face search."
        )

    # 2. Validasi Awal: Pastikan event ada
    event = await crud_event.get_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    # (Opsional) Pengecekan Status Indexing yang lebih baik
    # Daripada flag 'indexed_by_robota', kita bisa cek apakah jumlah gambar
    # sudah sama dengan jumlah wajah yang terindeks untuk event ini.
    # Untuk saat ini kita lewati agar tidak terlalu kompleks, tapi ini adalah ide untuk masa depan.

    # --- LOGIKA UTAMA BARU ---

    # 3. Dapatkan Vektor Wajah dari Foto Selfie Pengguna
    logger.info(f"Generating embedding for user {current_user.id}'s selfie...")
    # Ubah URL selfie menjadi path disk lokal
    selfie_path = current_user.selfie.replace(f"{settings.API_BASE_URL}/media/", settings.SELFIE_STORAGE_PATH, 1)
    try:
        # Jalankan DeepFace.represent yang berat di thread terpisah
        target_embedding_list = await run_in_threadpool(
            DeepFace.represent,
            img_path=selfie_path,
            model_name=settings.MODEL_NAME,  # Gunakan model yang konsisten
            enforce_detection=True
        )
        # Ambil vektor dari wajah pertama yang terdeteksi
        target_embedding = target_embedding_list[0]["embedding"]
    except Exception:
        # Ini terjadi jika tidak ada wajah terdeteksi di foto selfie
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find a face in your selfie. Please upload a clearer photo."
        )
    
    logger.info(f"Selfie embedding generated. Searching for similar faces in event {event_id}...")

    # 4. Panggil Service Pencarian Berbasis Database dengan Vektor Target
    # Service ini akan menjalankan query SELECT ... WHERE vector <=> ...
    matched_images_data = await face_recognition_service.find_similar_faces_in_db(
        db=db,
        event_id=event_id,
        target_embedding=target_embedding,
        threshold=0.6 # Ambang batas kemiripan, bisa diatur. Semakin kecil semakin mirip.
    )

    # 5. Kembalikan Hasilnya
    # Tidak perlu lagi proses manual, karena service sudah mengembalikan data jadi
    # dalam format list of dictionary yang cocok dengan skema MatchedImageResult.
    return matched_images_data