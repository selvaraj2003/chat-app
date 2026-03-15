from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.auth.routes import router as auth_router
from app.ai.routes import router as ai_router
import os

# Create tables 
Base.metadata.create_all(bind=engine)

# App 
app = FastAPI(
    title=settings["APP_NAME"],
    description=(
        "JWT-secured DevOps AI Chat Assistant powered by a cloud Ollama endpoint. "
        "Supports multi-turn conversations with full session history."
    ),
    version="2.0.0",
    docs_url="/docs" if settings["DEBUG"] else None,
    redoc_url="/redoc" if settings["DEBUG"] else None,
)

# CORS
origins = [o.strip() for o in os.environ["ALLOWED_ORIGINS"].split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],     
    allow_headers=["*"],
)

#  Routers 
app.include_router(auth_router)
app.include_router(ai_router)


#  Health check 
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": settings["APP_NAME"],
        "environment": settings["ENVIRONMENT"],
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}