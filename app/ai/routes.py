from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time
import uuid

from app.core.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatHistory
from app.ai.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.ai.client import cloud_chat, get_cloud_models

router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
    dependencies=[Depends(get_current_user)],
)

# GENERATE CLOUD CHAT
@router.post("/generate/cloud", response_model=ChatResponse)
def chat_with_cloud_ai(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return generate_chat(payload, db, current_user)


def generate_chat(payload: ChatRequest, db: Session, current_user: User):
    session_id = payload.session_id or str(uuid.uuid4())
    start_time = time.time()
    model_name = payload.model

    try:
        ai_response, tokens_used = cloud_chat(payload.prompt, model_name)

        latency_ms = int((time.time() - start_time) * 1000)

        chat = ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            prompt=payload.prompt,
            response=ai_response,
            model_name=model_name,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            is_success=True,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

        return ChatResponse(
            session_id=session_id,
            response=ai_response,
            model=model_name,
            latency_ms=latency_ms,
        )

    except Exception as e:
        db.add(ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            prompt=payload.prompt,
            response="",
            model_name=model_name,
            is_success=False,
            error_message=str(e),
        ))
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI processing failed")


# GET CHAT HISTORY
@router.get("/history")
def get_chat_history(session_id: str | None = None, limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id)
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


# DELETE CHAT SESSION
@router.delete("/history/{session_id}")
def delete_chat(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = db.query(ChatHistory).filter(ChatHistory.session_id == session_id, ChatHistory.user_id == current_user.id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    db.commit()
    return {"message": "Chat deleted successfully"}


# LIST CLOUD MODELS
@router.get("/models/cloud")
def list_cloud_models():
    return {
        "provider": "cloud",
        "default": settings["CLOUD_MODEL"],
        "models": get_cloud_models(),
    }