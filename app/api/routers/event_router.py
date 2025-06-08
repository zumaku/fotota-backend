# app/api/routers/event_router.py

import uuid
import math
from enum import Enum
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import crud_event, crud_image
from app.db.models import User as UserModel, Event as EventModel
from app.schemas import event_schema, pagination_schema, image_schema

router = APIRouter()

@router.post("", response_model=event_schema.EventPublic, status_code=status.HTTP_201_CREATED, summary="Create New Event")
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
    event = await crud_event.create_event(db=db, event_in=event_in, owner_id=admin_user.id)
    
    # Generate link unik setelah event dibuat dan memiliki ID
    unique_link = f"/events/{event.id}/{uuid.uuid4()}" # Contoh format link
    event_updated = await crud_event.update_event(db, event_db_obj=event, event_in=event_schema.EventUpdate(link=unique_link))
    
    return event_updated

@router.get("/search", response_model=List[event_schema.EventPublic], summary="Search for Events")
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
    return await crud_event.search_events_by_name(db=db, query=q)

@router.get("/my-events", response_model=List[event_schema.EventPublic], summary="Get Events Created by Me")
async def get_my_created_events(
    db: AsyncSession = Depends(deps.get_db_session),
    admin_user: UserModel = Depends(deps.get_current_admin_user)
):
    """
    Mengambil daftar semua event yang telah dibuat oleh admin yang sedang login.
    """
    return await crud_event.get_events_by_owner(db=db, owner_id=admin_user.id)

@router.get("/{event_id}", response_model=event_schema.EventPublic, summary="Get a Specific Event")
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
    return event

@router.put("/{event_id}", response_model=event_schema.EventPublic, summary="Update an Event")
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
    event = await crud_event.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.id_user != admin_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    await crud_event.delete_event(db=db, event_to_delete=event)
    

# Enum untuk validasi parameter sorting
class ImageSortBy(str, Enum):
    created_at = "created_at"
    file_name = "file_name"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/{event_id}/images", response_model=pagination_schema.PaginatedResponse[image_schema.ImagePublic], summary="Get Images in an Event with Pagination")
async def get_images_in_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    # Parameter query dengan validasi dan nilai default
    page: int = Query(1, gt=0, description="Halaman yang diminta"),
    limit: int = Query(10, gt=0, le=50, description="Jumlah item per halaman (max: 50)"),
    sort_by: ImageSortBy = Query(ImageSortBy.created_at, description="Field untuk sorting"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Urutan sorting"),
    search: Optional[str] = Query(None, min_length=2, description="Keyword pencarian nama file"),
    # Endpoint ini bisa diakses semua user yang login
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mengambil daftar gambar dari sebuah event dengan fitur lengkap:
    - **Pagination**: `page` dan `limit`
    - **Sorting**: `sort_by` (`created_at`, `file_name`) dan `sort_order` (`asc`, `desc`)
    - **Searching**: `search` (berdasarkan nama file)
    
    Endpoint ini bisa digunakan untuk mengimplementasikan "infinite scroll" di Flutter.
    """
    # Verifikasi dulu apakah event-nya ada
    event = await crud_event.get_event_by_id(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # TODO di masa depan: Tambahkan logika untuk memeriksa apakah user punya akses ke event ini (misal setelah memasukkan password)

    # Panggil fungsi CRUD yang canggih
    items, total_items = await crud_image.get_images_by_event_paginated(
        db=db,
        event_id=event_id,
        page=page,
        limit=limit,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        search=search
    )
    
    total_pages = math.ceil(total_items / limit)

    return pagination_schema.PaginatedResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        limit=limit,
        items=items
    )