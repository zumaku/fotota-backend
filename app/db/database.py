from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Buat engine async
# engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False) # echo=True untuk debug SQL
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False) # echo=True untuk debug SQL

# Buat session factory async
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False # Penting agar objek tetap bisa diakses setelah commit
)

# Dependensi untuk mendapatkan sesi DB di endpoint
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Tidak ada commit di sini, biarkan endpoint yang menangani
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()