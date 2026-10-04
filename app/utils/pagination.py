from pydantic import BaseModel
from typing import Generic, TypeVar, List
from math import ceil

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationMeta

    @classmethod
    def create(cls, data: List[T], page: int, limit: int, total: int):
        total_pages = ceil(total / limit) if limit > 0 else 0
        return cls(
            data=data,
            pagination=PaginationMeta(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages
            )
        )
