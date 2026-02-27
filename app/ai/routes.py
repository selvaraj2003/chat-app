from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
import time
import uuid

from app.core.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatHistory
from app.ai.schemas import ChatRequest, ChatResponse
from app.core.config import settings

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/generate", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI Chat API (JWT Protected)
    """

    session_id = payload.session_id or str(uuid.uuid4())
    start_time = time.time()

    try:
        # ==========================
        # Call Ollama
        # ==========================
        response = requests.post(
            settings["OLLAMA_BASE_URL"],
            json={
                "model": payload.model or settings["DEFAULT_MODEL"],
                "prompt": payload.prompt,
                "stream": False,
            },
            timeout=120
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Ollama service error"
            )

        data = response.json()
        ai_response = data.get("response", "")

        latency_ms = int((time.time() - start_time) * 1000)

        # ==========================
        # Save Chat History
        # ==========================
        chat = ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            prompt=payload.prompt,
            response=ai_response,
            model_name=payload.model or DEFAULT_MODEL,
            temperature=payload.temperature or 0.7,
            tokens_used=data.get("eval_count"),
            latency_ms=latency_ms,
            is_success=True
        )

        db.add(chat)
        db.commit()
        db.refresh(chat)

        return ChatResponse(
            session_id=session_id,
            response=ai_response,
            model=chat.model_name,
            latency_ms=latency_ms
        )

    except Exception as e:
        # ==========================
        # Save Failed Chat
        # ==========================
        chat = ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            prompt=payload.prompt,
            response="",
            model_name=payload.model or DEFAULT_MODEL,
            is_success=False,
            error_message=str(e)
        )

        db.add(chat)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI processing failed"
        )


@router.get("/history")
def get_chat_history(
    session_id: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get chat history (JWT Protected)
    """

    query = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    )

    if session_id:
        query = query.filter(ChatHistory.session_id == session_id)

    chats = query.order_by(ChatHistory.created_at.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "session_id": c.session_id,
            "prompt": c.prompt,
            "response": c.response,
            "model": c.model_name,
            "created_at": c.created_at,
        }
        for c in chats
    ]