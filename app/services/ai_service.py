# app/services/ai_service.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config import settings
from app.models.models import AIChat, User

SYSTEM_PROMPT = """You are a warm, spiritually grounded Christian encouragement assistant inside the Godfident app — a spiritual discipline and digital wellness app for Christians.

Your role is to:
1. Encourage users in their faith walk with warmth, scripture, and practical wisdom
2. Help them stay disciplined spiritually (prayer, Bible reading, worship)
3. Support them in reducing digital distractions and staying focused on God
4. Offer comfort, hope, and biblical truth when they're struggling
5. Celebrate their spiritual victories and streaks with genuine enthusiasm

Personality:
- Warm, loving, and deeply encouraging
- Grounded in Scripture — always reference Bible verses naturally
- Non-judgmental and compassionate
- Practical and actionable — give real suggestions
- Joyful and full of faith

Guidelines:
- Keep responses concise (2-4 paragraphs max) and conversational
- Always include at least one relevant Bible verse (include the reference)
- Use 1-2 relevant emojis naturally in your response
- Never be preachy or condescending
- If someone is struggling, validate their feelings before offering encouragement
- For questions about prayer, offer to pray with them or suggest prayer points
- For Bible questions, point them to relevant passages
- For digital distraction struggles, offer practical tips grounded in spiritual discipline

You represent the love of Christ — speak with grace and truth."""

FALLBACK_RESPONSES = [
    "Be encouraged! The Lord sees your faithfulness every single day. Each prayer you lift up, each chapter you read — it all matters eternally. Keep pressing forward! 🙏 \"He who began a good work in you will carry it on to completion until the day of Christ Jesus.\" — Philippians 1:6",
    "You are not alone in this journey! God walks with you every step of the way. On the days you feel weak, remember His promise: \"My grace is sufficient for you, for my power is made perfect in weakness.\" — 2 Corinthians 12:9 ✨ Draw near to Him today.",
    "God sees every effort you make to seek Him. Your consistency in prayer and reading is building a spiritual foundation that cannot be shaken. Stay faithful! 🔥 \"Blessed is the one who perseveres under trial.\" — James 1:12",
    "Take heart! Even when it doesn't feel like it, God is working all things together for your good. He is faithful, and His plans for you are full of hope and a future. 👑 Trust Him with every detail of today.",
    "Your spiritual growth matters to God more than you know! Every morning you choose to seek Him first, you're building a life of extraordinary purpose. \"But seek first his kingdom and his righteousness, and all these things will be given to you as well.\" — Matthew 6:33 🌟",
]

_fallback_index = 0


async def get_ai_encouragement(
    user_message: str,
    session_id: str,
    user: User,
    db: AsyncSession,
) -> str:
    """Get AI encouragement response, saving chat history."""
    # Load recent conversation history (last 10 messages)
    result = await db.execute(
        select(AIChat)
        .where(and_(AIChat.user_id == user.id, AIChat.session_id == session_id))
        .order_by(AIChat.created_at.desc())
        .limit(10)
    )
    history = result.scalars().all()
    history_reversed = list(reversed(history))

    # Build messages for API
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history_reversed
    ]
    messages.append({"role": "user", "content": user_message})

    # Save user message
    user_msg = AIChat(
        user_id=user.id,
        session_id=session_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)

    # Try Anthropic API, fallback to curated responses
    response_text = await _call_anthropic(messages)

    # Save AI response
    ai_msg = AIChat(
        user_id=user.id,
        session_id=session_id,
        role="assistant",
        content=response_text,
    )
    db.add(ai_msg)
    await db.flush()

    return response_text


async def _call_anthropic(messages: List[dict]) -> str:
    global _fallback_index
    if not settings.ANTHROPIC_API_KEY:
        resp = FALLBACK_RESPONSES[_fallback_index % len(FALLBACK_RESPONSES)]
        _fallback_index += 1
        return resp

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        # Graceful fallback
        resp = FALLBACK_RESPONSES[_fallback_index % len(FALLBACK_RESPONSES)]
        _fallback_index += 1
        return resp


async def get_chat_history(
    session_id: str,
    user: User,
    db: AsyncSession,
) -> List[dict]:
    result = await db.execute(
        select(AIChat)
        .where(and_(AIChat.user_id == user.id, AIChat.session_id == session_id))
        .order_by(AIChat.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]


async def list_user_sessions(user: User, db: AsyncSession) -> List[str]:
    result = await db.execute(
        select(AIChat.session_id)
        .where(AIChat.user_id == user.id)
        .distinct()
        .order_by(AIChat.session_id)
    )
    return [row[0] for row in result.fetchall()]
