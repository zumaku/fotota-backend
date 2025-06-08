from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import engine
from app.db.models import Base # Base dari user_model jika tidak pakai base_class
from app.api.routers import auth_router, user_router, event_router, image_router

# Fungsi untuk event startup dan shutdown (misalnya membuat tabel DB)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Buat tabel database (HANYA UNTUK PENGEMBANGAN, gunakan Alembic untuk produksi)
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Hati-hati, hapus semua tabel!
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created (if they didn't exist).")
    yield
    # Shutdown: (misalnya menutup koneksi pool jika diperlukan, tapi engine biasanya handle ini)
    print("Application shutdown.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/v1/openapi.json", # Sesuaikan path OpenAPI
    docs_url="/api/v1/docs",            # Sesuaikan path Swagger UI
    redoc_url="/api/v1/redoc",          # Sesuaikan path ReDoc
    lifespan=lifespan # Menggunakan lifespan manager baru di FastAPI
)

# --- MOUNTING UNTUK STATIC FILES ---
# Ini memberitahu FastAPI bahwa setiap request ke path yang berawalan "/media"
# harus disajikan sebagai file langsung dari direktori "storage".
app.mount("/media", StaticFiles(directory="storage"), name="media")
# ---------------------------------------------

# Sertakan router
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(event_router.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(image_router.router, prefix="/api/v1/images", tags=["Images"])

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}

# Untuk menjalankan: uvicorn app.main:app --reload --port 8000