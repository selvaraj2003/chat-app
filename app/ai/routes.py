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
from fastapi import UploadFile, File
from app.ai.image_helpers import save_image,extract_text_fast,extract_text_easyocr,image_to_base64
from fastapi import Form
import json

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



@router.post("/upload/image", response_model=ChatResponse)
def upload_and_process_image(
    file: UploadFile = File(...),
    inputjson: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()

    try:
        data = {}
        if inputjson:
            try:
                data = json.loads(inputjson)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")

        user_prompt = data.get("prompt", "Analyze this file")
        model_name = data.get("model", settings["CLOUD_MODEL"])
        session_id = data.get("session_id") or str(uuid.uuid4())

     
        file_path = save_image(file)
        ext = file.filename.split(".")[-1].lower()

        extracted_text = ""

      
        if ext in ["jpg", "jpeg", "png"]:
            try:
                image_b64 = image_to_base64(file_path)

                ai_response, tokens_used = cloud_chat(
                    prompt=user_prompt,
                    image_base64=image_b64,
                    model=model_name
                )

                latency_ms = int((time.time() - start_time) * 1000)

                db.add(ChatHistory(
                    user_id=current_user.id,
                    session_id=session_id,
                    prompt=user_prompt,
                    response=ai_response,
                    model_name=model_name,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    is_success=True,
                ))
                db.commit()

                return ChatResponse(
                    session_id=session_id,
                    response=ai_response,
                    model=model_name,
                    latency_ms=latency_ms,
                )

            except Exception as e:
                print("AI Vision failed → fallback OCR:", str(e))

     
        extracted_text = extract_text_fast(file_path)

     
        if not extracted_text.strip() and ext in ["jpg", "jpeg", "png"]:
            extracted_text = extract_text_easyocr(file_path)

        if not extracted_text:
            extracted_text = "No readable content found"

       
        prompt = f"""
        Summarize the following content:

        {extracted_text}

        User request:
        {user_prompt}
        """

        ai_response, tokens_used = cloud_chat(prompt, model_name)

        latency_ms = int((time.time() - start_time) * 1000)

        db.add(ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            prompt=user_prompt,
            response=ai_response,
            model_name=model_name,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            is_success=True,
        ))
        db.commit()

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
            prompt="FILE_UPLOAD",
            response="",
            model_name=data.get("model", "UNKNOWN"),
            is_success=False,
            error_message=str(e),
        ))
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))