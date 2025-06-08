# app/schemas/pagination_schema.py

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

# Membuat tipe generik yang bisa menampung skema apapun (misal: ImagePublic)
DataType = TypeVar('DataType')

class PaginatedResponse(BaseModel, Generic[DataType]):
    '''
    Skema untuk Respons Berhalaman (Pagination)
    Saat mengembalikan data yang dibagi per halaman, praktik terbaik adalah
    tidak hanya mengembalikan daftar item, tetapi juga metadata tentang halaman
    itu sendiri (total item, total halaman, dll.). Ini akan sangat membantu tim Flutter.
    '''
    total_items: int = Field(..., description="Jumlah total item di database")
    total_pages: int = Field(..., description="Jumlah total halaman yang tersedia")
    current_page: int = Field(..., description="Halaman saat ini")
    limit: int = Field(..., description="Jumlah item per halaman")
    items: List[DataType] = Field(..., description="Daftar item untuk halaman ini")