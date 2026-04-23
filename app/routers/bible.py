# app/routers/bible.py
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User, VerseBookmark, VerseHighlight
from app.schemas.schemas import (
    VerseOfDay, BibleSearchResult, BookmarkCreate, BookmarkOut,
    HighlightCreate, HighlightOut, MessageResponse
)
from app.services.auth_service import get_current_user
from app.services.bible_service import (
    get_verse_of_day, get_chapter, search_verses,
    get_books_list, get_random_inspirational_verse
)

router = APIRouter(prefix="/bible", tags=["Bible"])


@router.get("/verse-of-day", response_model=VerseOfDay)
async def verse_of_day():
    return get_verse_of_day()


@router.get("/inspiration")
async def random_inspiration():
    return get_random_inspirational_verse()


@router.get("/books")
async def list_books():
    return get_books_list()


@router.get("/chapter/{book}/{chapter}")
async def read_chapter(
    book: str = Path(..., description="Book name e.g. Psalms"),
    chapter: int = Path(..., ge=1, description="Chapter number"),
):
    verses = get_chapter(book, chapter)
    if verses is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chapter not found: {book} {chapter}. Available books have sample chapters loaded."
        )
    return {
        "book": book,
        "chapter": chapter,
        "verse_count": len(verses),
        "verses": verses,
    }


@router.get("/search", response_model=BibleSearchResult)
async def search_bible(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=20, le=50),
):
    results = search_verses(q, limit)
    return BibleSearchResult(results=results, total=len(results), query=q)


# ─── Bookmarks ───

@router.get("/bookmarks", response_model=List[BookmarkOut])
async def get_bookmarks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VerseBookmark)
        .where(VerseBookmark.user_id == current_user.id)
        .order_by(VerseBookmark.created_at.desc())
    )
    return result.scalars().all()


@router.post("/bookmarks", response_model=BookmarkOut, status_code=201)
async def add_bookmark(
    payload: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for duplicate
    result = await db.execute(
        select(VerseBookmark).where(
            and_(
                VerseBookmark.user_id == current_user.id,
                VerseBookmark.book == payload.book,
                VerseBookmark.chapter == payload.chapter,
                VerseBookmark.verse_number == payload.verse_number,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing  # Idempotent

    bookmark = VerseBookmark(user_id=current_user.id, **payload.model_dump())
    db.add(bookmark)
    await db.flush()
    return bookmark


@router.delete("/bookmarks/{bookmark_id}", response_model=MessageResponse)
async def remove_bookmark(
    bookmark_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VerseBookmark).where(
            and_(VerseBookmark.id == bookmark_id, VerseBookmark.user_id == current_user.id)
        )
    )
    bm = result.scalar_one_or_none()
    if not bm:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await db.delete(bm)
    return MessageResponse(message="Bookmark removed")


# ─── Highlights ───

@router.get("/highlights", response_model=List[HighlightOut])
async def get_highlights(
    book: Optional[str] = Query(None),
    chapter: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(VerseHighlight).where(VerseHighlight.user_id == current_user.id)
    if book:
        query = query.where(VerseHighlight.book == book)
    if chapter:
        query = query.where(VerseHighlight.chapter == chapter)
    result = await db.execute(query.order_by(VerseHighlight.created_at.desc()))
    return result.scalars().all()


@router.post("/highlights", response_model=HighlightOut, status_code=201)
async def add_highlight(
    payload: HighlightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for existing, update color if so
    result = await db.execute(
        select(VerseHighlight).where(
            and_(
                VerseHighlight.user_id == current_user.id,
                VerseHighlight.book == payload.book,
                VerseHighlight.chapter == payload.chapter,
                VerseHighlight.verse_number == payload.verse_number,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.color = payload.color
        return existing

    highlight = VerseHighlight(user_id=current_user.id, **payload.model_dump())
    db.add(highlight)
    await db.flush()
    return highlight


@router.delete("/highlights/{highlight_id}", response_model=MessageResponse)
async def remove_highlight(
    highlight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VerseHighlight).where(
            and_(VerseHighlight.id == highlight_id, VerseHighlight.user_id == current_user.id)
        )
    )
    hl = result.scalar_one_or_none()
    if not hl:
        raise HTTPException(status_code=404, detail="Highlight not found")
    await db.delete(hl)
    return MessageResponse(message="Highlight removed")
