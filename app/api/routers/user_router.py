from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models.user_model import User as UserModel
from app.schemas import user_schema

router = APIRouter()

@router.get("/me", response_model=user_schema.UserPublic, summary="Get Current User Information")
async def read_current_user(
    current_user: UserModel = Depends(deps.get_current_active_user)
):
    """
    Ambil informasi tentang pengguna yang saat ini terautentikasi.
    """
    return current_user