from typing import Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.db.models.user_model import User as UserModel
from app.schemas.user_schema import UserCreateGoogle

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
    try:
        return await db.get(UserModel, user_id)
    except SQLAlchemyError as e:
        print(f"Database error in get_user_by_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user by ID.")

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    try:
        result = await db.execute(select(UserModel).filter(UserModel.email == email))
        return result.scalars().first()
    except SQLAlchemyError as e:
        print(f"Database error in get_user_by_email: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user by email.")


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[UserModel]:
    try:
        result = await db.execute(select(UserModel).filter(UserModel.google_id == google_id))
        return result.scalars().first()
    except SQLAlchemyError as e:
        print(f"Database error in get_user_by_google_id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user by Google ID.")

async def create_google_user(db: AsyncSession, user_in: UserCreateGoogle) -> UserModel:
    try:
        db_user = UserModel(
            email=user_in.email,
            name=user_in.name,
            picture=user_in.picture,
            google_id=user_in.google_id,
            google_refresh_token=user_in.google_refresh_token
            # internal_refresh_token_hash akan diisi nanti
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e: # Misal IntegrityError jika email/google_id sudah ada
        await db.rollback()
        print(f"Database error in create_google_user: {e}")
        # Cek apakah ini karena duplikasi dan coba get user jika iya
        existing_user = await get_user_by_google_id(db, google_id=user_in.google_id)
        if existing_user: return existing_user # Jika race condition, user sudah dibuat
        existing_user_email = await get_user_by_email(db, email=user_in.email)
        if existing_user_email: return existing_user_email # Jika race condition, user sudah dibuat
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Could not create user. It might already exist or database error: {str(e)}")

async def update_user(
    db: AsyncSession,
    user: UserModel, # User object yang sudah ada dari DB
    data_to_update: Dict[str, Any]
) -> UserModel:
    try:
        for field, value in data_to_update.items():
            if hasattr(user, field):
                setattr(user, field, value)
        # user.updated_at = datetime.now(timezone.utc) # Jika tidak pakai onupdate dari model
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Database error in update_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating user data: {str(e)}")