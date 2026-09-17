import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_role
from app.core.embeddings import embed_text
from app.database import get_db
from app.models.enums import UserRole
from app.models.menu import MenuCategory, MenuItem
from app.schemas.menu import (
    MenuCategoryOut,
    MenuItemCreate,
    MenuItemOut,
    MenuItemUpdate,
    MenuSearchResult,
)
from app.services.menu import search_menu_items

router = APIRouter(prefix="/menu", tags=["menu"])


def _embeddable_text(name: str, description: str | None) -> str:
    return f"{name}. {description}" if description else name


@router.get("", response_model=list[MenuCategoryOut])
async def list_menu(db: AsyncSession = Depends(get_db)) -> list[MenuCategory]:
    result = await db.execute(
        select(MenuCategory)
        .options(selectinload(MenuCategory.items))
        .order_by(MenuCategory.display_order, MenuCategory.name)
    )
    return list(result.scalars().all())


@router.get("/search", response_model=list[MenuSearchResult])
async def search_menu(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> list[MenuSearchResult]:
    matches = await search_menu_items(db, q, limit)
    return [MenuSearchResult(item=MenuItemOut.model_validate(item), score=score) for item, score in matches]


@router.post(
    "/items",
    response_model=MenuItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def create_menu_item(payload: MenuItemCreate, db: AsyncSession = Depends(get_db)) -> MenuItem:
    category = await db.get(MenuCategory, payload.category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu category not found")

    embedding = await embed_text(_embeddable_text(payload.name, payload.description))
    item = MenuItem(**payload.model_dump(), embedding=embedding)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put(
    "/items/{item_id}",
    response_model=MenuItemOut,
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def update_menu_item(
    item_id: uuid.UUID, payload: MenuItemUpdate, db: AsyncSession = Depends(get_db)
) -> MenuItem:
    item = await db.get(MenuItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    updates = payload.model_dump(exclude_unset=True)

    if "category_id" in updates:
        category = await db.get(MenuCategory, updates["category_id"])
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu category not found")

    regenerate_embedding = "name" in updates or "description" in updates

    for field, value in updates.items():
        setattr(item, field, value)

    if regenerate_embedding:
        item.embedding = await embed_text(_embeddable_text(item.name, item.description))

    await db.commit()
    await db.refresh(item)
    return item


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def delete_menu_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    item = await db.get(MenuItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    await db.delete(item)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Menu item cannot be deleted because it is referenced by existing orders",
        ) from exc
