# src/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import structlog

from src.core.database import get_db
from src.models import User
from src.schemas.user import UserCreate, UserResponse, UserUpdate

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех пользователей"""
    logger.info("Getting users list", skip=skip, limit=limit)
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: uuid.UUID,
        db: AsyncSession = Depends(get_db)
):
    """Получить пользователя по ID"""
    logger.info("Getting user", user_id=str(user_id))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("User not found", user_id=str(user_id))
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
        user: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """Создать нового пользователя"""
    logger.info("Creating user", username=user.username)

    # Проверка уникальности
    existing = await db.execute(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )
    if existing.scalar_one_or_none():
        logger.warning("User already exists", username=user.username)
        raise HTTPException(status_code=400, detail="Username or email already exists")

    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    logger.info("User created", user_id=str(db_user.id))
    return db_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: uuid.UUID,
        user_update: UserUpdate,
        db: AsyncSession = Depends(get_db)
):
    """Обновить данные пользователя"""
    logger.info("Updating user", user_id=str(user_id))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name

    await db.commit()
    await db.refresh(user)

    logger.info("User updated", user_id=str(user_id))
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
        user_id: uuid.UUID,
        db: AsyncSession = Depends(get_db)
):
    """Удалить пользователя"""
    logger.info("Deleting user", user_id=str(user_id))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    logger.info("User deleted", user_id=str(user_id))
    return None