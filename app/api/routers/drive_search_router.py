# app/api/routers/drive_search_router.py

import re
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_drive_search
from app.db.models import User as UserModel
from app.schemas import drive_search_schema
from app.services import drive_service

router = APIRouter()

def _extract_folder_id(url: str) -> str:
    """Mengekstrak folder ID dari berbagai format URL Google Drive."""
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    raise HTTPException(status_code=400, detail="Invalid Google Drive folder URL format.")


@router.post("", response_model=drive_search_schema.DriveSearchCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_drive_search(
    *,
    request_data: drive_search_schema.DriveSearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Memulai sesi pencarian wajah di sebuah folder Google Drive.
    Proses akan berjalan di latar belakang.
    """
    if not current_user.selfie:
        raise HTTPException(status_code=400, detail="Please upload a selfie first.")

    folder_id = _extract_folder_id(str(request_data.drive_url))
    
    # Buat record pencarian di database
    new_search = await crud_drive_search.create_drive_search(db, user_id=current_user.id, folder_id=folder_id)

    # Jadwalkan tugas berat di latar belakang
    background_tasks.add_task(
        drive_service.run_drive_search_and_save,
        search_id=new_search.id,
        folder_id=folder_id,
        user_selfie_url=current_user.selfie
    )

    return drive_search_schema.DriveSearchCreateResponse(
        search_id=new_search.id,
        status=new_search.status,
        message="Search has been initiated. Check back later for results."
    )

@router.get("/{search_id}", response_model=drive_search_schema.DriveSearchResultResponse)
async def get_search_results(
    search_id: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mengambil status dan hasil dari sebuah sesi pencarian.
    """
    search_session = await crud_drive_search.get_drive_search_results(db, search_id=search_id)

    if not search_session:
        raise HTTPException(status_code=404, detail="Search session not found.")
    if search_session.id_user != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view these results.")

    return drive_search_schema.DriveSearchResultResponse(
        search_id=search_session.id,
        status=search_session.status,
        drive_folder_id=search_session.drive_folder_id,
        created_at=search_session.created_at,
        results=search_session.found_images
    )