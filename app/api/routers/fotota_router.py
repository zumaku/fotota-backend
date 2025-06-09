# app/api/routers/fotota_router.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.api import deps
from app.crud import crud_fotota, crud_image
from app.db.models import User as UserModel, Image as ImageModel
from app.schemas import fotota_schema

router = APIRouter()

@router.post("", response_model=List[fotota_schema.FototaPublic], status_code=status.HTTP_201_CREATED, summary="Bookmark One or More Photos")
async def bookmark_photos_in_bulk(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    # Gunakan skema bulk yang baru
    bookmarks_in: fotota_schema.FototaBulkCreate,
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Menambahkan satu atau lebih foto ke koleksi "Fotota" milik pengguna.
    Kirimkan sebuah JSON dengan key "image_ids" yang berisi array of integer.
    """
    # TODO: Validasi apakah semua image_ids ada di database
    
    new_bookmarks = await crud_fotota.bulk_create_bookmarks(
        db, user_id=current_user.id, image_ids=bookmarks_in.image_ids
    )
    
    # Eager load relasi image untuk setiap bookmark baru sebelum dikembalikan
    for bm in new_bookmarks:
        await db.refresh(bm, attribute_names=["image"])
        
    return new_bookmarks

@router.get("", response_model=List[fotota_schema.BookmarkedEventGroup], summary="Get My Bookmarked Photos (Grouped by Event)")
async def get_my_bookmarked_photos(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mengambil semua foto yang telah di-bookmark oleh pengguna,
    diurutkan dari yang terbaru dan dikelompokkan berdasarkan event.
    """
    all_bookmarks = await crud_fotota.get_all_bookmarked_by_user(db, user_id=current_user.id)
    
    # Logika untuk mengelompokkan hasil berdasarkan event di sisi Python
    events_dict = defaultdict(lambda: {"event_id": None, "event_name": None, "event_date": None, "bookmarked_photos": []})
    
    for bookmark in all_bookmarks:
        event = bookmark.image.event
        if events_dict[event.id]["event_id"] is None:
            events_dict[event.id]["event_id"] = event.id
            events_dict[event.id]["event_name"] = event.name
            events_dict[event.id]["event_date"] = event.date
        
        events_dict[event.id]["bookmarked_photos"].append(bookmark)
        
    return list(events_dict.values())

@router.delete("", status_code=status.HTTP_200_OK, summary="Remove One or More Bookmarks")
async def remove_bookmarks_in_bulk(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    # Ambil daftar ID dari query parameter, bukan dari path
    ids: List[int] = Query(..., description="A list of bookmark IDs to delete"),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Menghapus satu atau lebih foto dari koleksi "Fotota" (bookmark).
    Kirimkan daftar ID bookmark sebagai query parameter (contoh: ?ids=1&ids=3&ids=5).
    """
    deleted_count = await crud_fotota.bulk_delete_bookmarks_by_ids(
        db, user_id=current_user.id, bookmark_ids=ids
    )
    
    if deleted_count == 0:
        # Ini bisa terjadi jika ID tidak ditemukan atau bukan milik user tersebut
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching bookmarks found to delete.")
        
    return {"message": f"Successfully deleted {deleted_count} bookmark(s)."}