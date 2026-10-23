import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure root paths are accessible
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ROOT_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(ROOT_DIR / "cosmos_shorts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "cosmos_shorts"))
if str(ROOT_DIR / "MoneyPrinterTurbo") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "MoneyPrinterTurbo"))

from backend.config import FRONTEND_DIR, HOST, PORT, TOKEN_FILE
from backend.database import init_db
from backend.routers import health, youtube, studio, video, calendar, analytics, categories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cosmos.app")

app = FastAPI(
    title="COSMOS GROWTH OS",
    description="Premium YouTube Analytics, AI Content Studio, Scheduling & Automation Platform",
    version="1.0.0"
)

# CORS restricted to localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8500", "http://localhost:8500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(youtube.router)
app.include_router(studio.router)
app.include_router(categories.router)
app.include_router(video.router)
app.include_router(calendar.router)
app.include_router(analytics.router)

# Mount frontend static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.on_event("startup")
def startup_event():
    logger.info("Initializing COSMOS GROWTH OS Database...")
    init_db()
    
    # Auto sync channel info if token is available
    if TOKEN_FILE.exists():
        try:
            logger.info("Syncing YouTube Channel data on boot...")
            youtube.sync_channel_data()
        except Exception as e:
            logger.warning(f"Could not auto-sync YouTube on startup: {e}")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_file))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Launching COSMOS GROWTH OS at http://{HOST}:{PORT}")
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=False)
