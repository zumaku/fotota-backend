# app/api/routers/activity_router.py

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_activity
from app.db.models import User as UserModel
from app.schemas import event_schema
# Kita akan butuh helper function yang sama dengan di event_router
from app.api.routers.event_router import get_image_previews 

router = APIRouter()

@router.get("/me/recent", response_model=List[event_schema.EventPublicSummary], summary="Get My Recently Accessed Events")
async def get_my_recent_activities(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Mengambil 5 event terakhir yang diakses oleh pengguna yang sedang login.
    Ini adalah data untuk halaman beranda.
    """
    events = await crud_activity.get_recent_accessed_events_for_user(db=db, user_id=current_user.id, limit=5)
    
    # Kita perlu membuat images_preview secara manual, sama seperti sebelumnya
    for event in events:
        event.images_preview = get_image_previews(event)

    return events