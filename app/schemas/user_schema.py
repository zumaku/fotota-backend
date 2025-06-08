from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Properti dasar yang dimiliki user
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    name: Optional[str] = Field(None, example="John Doe")
    picture: Optional[str] = Field(None, example="https://.../photo.jpg")

# Properti yang diterima saat membuat user baru via Google
class UserCreateGoogle(UserBase):
    google_id: str = Field(..., example="google_user_id_string")
    google_refresh_token: Optional[str] = None # Refresh token dari Google (jika didapat)

# Properti tambahan yang disimpan di DB tetapi tidak selalu dikembalikan semua
class UserInDBBase(UserBase):
    id: int
    google_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Menggantikan orm_mode di Pydantic V2

# Properti yang dikembalikan ke client (tanpa data sensitif)
class UserPublic(UserBase):
    id: int
    is_admin: bool
    selfie: Optional[str] = None
    created_at: datetime
    # 'name' dan 'picture' sudah diwarisi dari UserBase

    class Config:
        from_attributes = True
        
class UserInfo(BaseModel):
    """Skema sederhana untuk menampilkan info pemilik event."""
    id: int
    name: Optional[str] = None
    picture: Optional[str] = None

    class Config:
        from_attributes = True