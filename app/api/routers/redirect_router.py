# app/api/routers/redirect_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_event
from app.core.config import settings

router = APIRouter()

@router.get("/{share_code}", summary="Redirect to App Deep Link")
async def redirect_to_app(
    share_code: str,
    db: AsyncSession = Depends(deps.get_db_session)
):
    """
    Menerima share code, mencari event yang sesuai, lalu mengarahkan
    pengguna ke deep link aplikasi Flutter.
    """
    # 1. Cari event berdasarkan share_code
    event = await crud_event.get_event_by_share_code(db, share_code=share_code)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event link is not valid or has expired.")

    # 2. Bangun URL deep link Flutter yang sebenarnya
    deep_link_url = f"{settings.DEEP_LINK_BASE_URL}/{event.id}"

    # 3. Kembalikan respons redirect
    return RedirectResponse(url=deep_link_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
