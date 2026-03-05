import requests
from fastapi import HTTPException
from app.core.config import settings

def ollama_call(prompt: str, model: str | None):
    r = requests.post(
        settings['OLLAMA_BASE_URL'],
        json={
            "model": model or settings["DEFAULT_OLLAMA_MODEL"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        },
        timeout=float(settings["OLLAMA_TIMEOUT"])
    )
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Ollama error")
    d = r.json()
    return d["message"]["content"], d.get("eval_count")

import requests
from fastapi import HTTPException

def cloud_call(prompt: str, model: str | None):
    r = requests.post(
        f"{settings['CLOUD_API_BASE_URL']}/api/generate",
        headers={
            "Authorization": f"Bearer {settings['CLOUD_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or settings["DEFAULT_CLOUD_MODEL"],
            "prompt": prompt,
            "stream": False,
        },
        timeout=300 
    )

    if r.status_code != 200:
        print(f"Cloud API Error: {r.status_code} - {r.text}")
        raise HTTPException(
            status_code=502,
            detail="Ollama Cloud service unavailable"
        )

    try:
        data = r.json()
        return data["response"], data.get("eval_count", 0)
    except Exception as e:
        print("JSON parse error:", e)
        raise HTTPException(
            status_code=500,
            detail="Invalid response format from Ollama Cloud"
        )
    
def get_local_models():
    r = requests.get(settings["OLLAMA_BASE_URL"].replace("/api/chat", "/api/tags"))
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch local models")
    return [m["name"] for m in r.json()["models"]]

def get_cloud_models():
    r = requests.get(f"{settings['CLOUD_API_BASE_URL']}/api/tags")
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch cloud models")
    return [m["name"] for m in r.json().get("models", [])]