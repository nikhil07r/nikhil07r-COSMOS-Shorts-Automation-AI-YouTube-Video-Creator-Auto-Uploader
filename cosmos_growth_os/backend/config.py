import os
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"

# Subsystems
COSMOS_SHORTS_DIR = ROOT_DIR / "cosmos_shorts"
MPT_DIR = ROOT_DIR / "MoneyPrinterTurbo"
LIB_DIR = ROOT_DIR / "lib"
PYTHON_BIN = LIB_DIR / "python" / "python.exe"
FFMPEG_BIN = LIB_DIR / "ffmpeg" / "ffmpeg-7.0-essentials_build" / "ffmpeg.exe"

# Database
DB_PATH = DATA_DIR / "cosmos_growth_os.db"

# YouTube Secrets
TOKEN_FILE = COSMOS_SHORTS_DIR / "token.json"
CLIENT_SECRET_FILE = COSMOS_SHORTS_DIR / "client_secret.json"

# Ollama Config
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = "qwen2.5:7b"
FALLBACK_MODEL = "qwen2.5:3b"

# Host & Port
HOST = "127.0.0.1"
PORT = 8500

# Channel Config
DEFAULT_CHANNEL_HANDLE = "@cosmos-1nr"
DEFAULT_VOICE = "hi-IN-MadhurNeural"
