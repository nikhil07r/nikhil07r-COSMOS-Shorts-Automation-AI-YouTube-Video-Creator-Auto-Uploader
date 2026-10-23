import shutil
import urllib.request
import json
import logging
from fastapi import APIRouter
from backend.config import OLLAMA_BASE_URL, FFMPEG_BIN, TOKEN_FILE, CLIENT_SECRET_FILE, ROOT_DIR

router = APIRouter(prefix="/api/health", tags=["health"])
logger = logging.getLogger("cosmos.health")

@router.get("")
def get_system_health():
    # 1. Ollama check
    ollama_status = {"status": "offline", "models": []}
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "COSMOS-Growth-OS"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            ollama_status = {"status": "online", "models": models}
    except Exception as e:
        ollama_status = {"status": "offline", "error": str(e), "models": []}

    # 2. FFmpeg check
    ffmpeg_ok = FFMPEG_BIN.exists()
    
    # 3. YouTube Auth check
    yt_auth_ok = TOKEN_FILE.exists()
    client_secret_ok = CLIENT_SECRET_FILE.exists()

    # 4. Disk space
    total, used, free = shutil.disk_usage(str(ROOT_DIR))
    free_gb = round(free / (2**30), 2)
    total_gb = round(total / (2**30), 2)

    return {
        "ollama": ollama_status,
        "ffmpeg": {"installed": ffmpeg_ok, "path": str(FFMPEG_BIN) if ffmpeg_ok else None},
        "youtube_auth": {
            "token_present": yt_auth_ok,
            "client_secret_present": client_secret_ok,
            "ready": yt_auth_ok
        },
        "disk": {
            "free_gb": free_gb,
            "total_gb": total_gb,
            "low_space": free_gb < 5.0
        },
        "all_systems_ready": (ollama_status["status"] == "online") and ffmpeg_ok and yt_auth_ok
    }
