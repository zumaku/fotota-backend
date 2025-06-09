# app/api/routers/fotota_router.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.api import deps
from app.crud import crud_fotota, crud_image
from app.db.models import User as UserModel, Image as ImageModel
from app.schemas import fotota_schema

router = APIRouter()

@router.post("", response_model=fotota_schema.FototaPublic, status_code=status.HTTP_201_CREATED, summary="Bookmark a Photo")
async def bookmark_photo(
    *,
    db: AsyncSession = Depends(deps.get_db_session),
    bookmark_in: fotota_schema.FototaCreate,
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Menambahkan sebuah foto ke koleksi "Fotota" (bookmark) milik pengguna.
    """
    image_id = bookmark_in.image_id
    # 1. Pastikan gambar ada
    image = await db.get(ImageModel, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    # 2. Pastikan user belum mem-bookmark gambar ini sebelumnya
    existing_bookmark = await crud_fotota.get_bookmark(db, user_id=current_user.id, image_id=image_id)
    if existing_bookmark:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This image is already bookmarked.")

    # TODO: Tambahkan validasi apakah user punya akses ke event dari gambar ini

    # 3. Buat bookmark
    new_bookmark = await crud_fotota.create_bookmark(db, user_id=current_user.id, image_id=image_id)
    
    # Eager load relasi image untuk respons
    await db.refresh(new_bookmark, attribute_names=["image"])
    
    return new_bookmark

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

@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a Bookmark")
async def remove_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Menghapus sebuah foto dari koleksi "Fotota" (bookmark).
    """
    bookmark = await crud_fotota.get_bookmark_by_id(db, bookmark_id=bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found.")
    
    # Pastikan hanya pemilik bookmark yang bisa menghapusnya
    if bookmark.id_user != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")
    
    await crud_fotota.delete_bookmark(db, bookmark_to_delete=bookmark)
    return None