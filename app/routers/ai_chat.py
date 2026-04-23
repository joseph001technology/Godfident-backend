# app/routers/ai_chat.py
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import AIChatMessage, AIChatResponse, AIChatHistory
from app.services.auth_service import get_current_user
from app.services.ai_service import (
    get_ai_encouragement, get_chat_history, list_user_sessions
)

router = APIRouter(prefix="/ai", tags=["AI Encouragement"])


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = payload.session_id or str(uuid.uuid4())
    response_text = await get_ai_encouragement(
        user_message=payload.message,
        session_id=session_id,
        user=current_user,
        db=db,
    )
    return AIChatResponse(
        session_id=session_id,
        response=response_text,
        role="assistant",
        created_at=datetime.now(timezone.utc),
    )


@router.get("/chat/sessions", response_model=List[str])
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_user_sessions(current_user, db)


@router.get("/chat/{session_id}/history", response_model=AIChatHistory)
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = await get_chat_history(session_id, current_user, db)
    return AIChatHistory(session_id=session_id, messages=messages)
