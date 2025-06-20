from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.model_loader import face_app
from app.db.database import engine
from app.db.models import Base # Base dari user_model jika tidak pakai base_class
from app.api.routers import auth_router, user_router, event_router, image_router, activity_router, fotota_router, redirect_router

# Fungsi untuk event startup dan shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Kode yang berjalan saat STARTUP ---
    
    print("Application startup: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Application startup: Database tables checked/created.")
    
    # Panggil salah satu fungsinya untuk memicu inisialisasi awal
    print("🔥 Initializing and warming up Insightface models...")
    # Cukup dengan mengimpor 'face_app' di atas, model sudah akan mulai dimuat.
    # Baris ini hanya untuk memastikan dan memberi log yang jelas.
    if face_app.app is None:
        print("Face analysis model failed to load. Application might not function correctly.")
    
    yield # Aplikasi siap

    # ... (kode shutdown)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/openapi.json", # Sesuaikan path OpenAPI
    docs_url="/docs",            # Sesuaikan path Swagger UI
    redoc_url="/redoc",          # Sesuaikan path ReDoc
    lifespan=lifespan # Menggunakan lifespan manager baru di FastAPI
)

# Sertakan router
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router.router, prefix="/users", tags=["Users"])
app.include_router(event_router.router, prefix="/events", tags=["Events"])
app.include_router(image_router.router, prefix="/images", tags=["Images"])
app.include_router(activity_router.router, prefix="/activity", tags=["Activity"])
app.include_router(fotota_router.router, prefix="/fotota", tags=["Fotota"])
app.include_router(redirect_router.router, prefix="/r", tags=["Redirect"])

@app.get('/', tags=["Welcome"])
async def welcome_message():
    """
    Endpoint selamat datang untuk API FotoTa.
    Memberikan informasi dasar tentang API.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API!",
        "version": settings.PROJECT_VERSION,
        "documentation_url": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}

# Install Dependensi: pip install aiofiles asyncpg fastapi httpx insightface python-jose opencv-python onnxruntime pydantic_settings pydantic[email] python-multipart SQLAlchemy uvicorn
# Untuk menjalankan: uvicorn app.main:app  --port 8000 --reload