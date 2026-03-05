from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.auth.routes import router as auth_router
from app.ai.routes import router as ai_router
import os

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Chat Assitance",
    description="JWT-secured AI chat backend using FastAPI, MySQL, and Ollama",
    version="1.0.0",
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

app.include_router(auth_router)
app.include_router(ai_router)

# Status
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Chat Assitance Backend is running"
    }