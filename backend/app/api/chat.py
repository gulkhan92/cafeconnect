from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_optional
from app.core.limiter import limiter
from app.core.llm.router import LLMRouter, get_llm_router
from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chatbot import handle_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    llm_router: LLMRouter = Depends(get_llm_router),
) -> ChatMessageResponse:
    return await handle_chat_message(db, llm_router, payload.session_id, payload.message, current_user)
