from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.categories import Category as CategoryModel
from app.shemas import Category as CategorySchema, CategoryCreate
from app.db_depends import get_async_db


# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)






