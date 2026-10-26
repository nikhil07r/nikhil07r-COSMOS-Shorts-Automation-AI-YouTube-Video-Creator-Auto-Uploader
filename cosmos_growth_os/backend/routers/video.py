import os
import sys
import threading
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.config import ROOT_DIR, COSMOS_SHORTS_DIR, DB_PATH
from backend.database import create_job, update_job, get_job, get_jobs

router = APIRouter(prefix="/api/video", tags=["video"])
logger = logging.getLogger("cosmos.video")

# Ensure cosmos_shorts is in sys.path
if str(COSMOS_SHORTS_DIR) not in sys.path:
    sys.path.insert(0, str(COSMOS_SHORTS_DIR))
if str(ROOT_DIR / "MoneyPrinterTurbo") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "MoneyPrinterTurbo"))

class StartVideoRequest(BaseModel):
    draft_id: Optional[str] = None
    title: Optional[str] = "COSMOS Short"
    category: Optional[str] = "Space & Universe"
    category_id: Optional[str] = None
    hindi_script: Optional[str] = ""
    keywords: Optional[list] = []
    mode: Optional[str] = "story"
    theme_color: Optional[str] = None
    language: Optional[str] = "hindi"
    subtitle_position_y: Optional[float] = 76.0
    preferred_model: Optional[str] = "qwen2.5:7b"

def run_pipeline_thread(job_id: str, topic_data: Dict[str, Any], theme_color: Optional[str], subtitle_pos: float, preferred_model: Optional[str]):
    try:
        def on_progress(pct: int, step_desc: str):
            update_job(job_id, status="processing", progress_pct=pct, current_step=step_desc)

        on_progress(15, "Initializing AI content & story directives")
        
        from cosmos_orchestrator import run_cosmos_short_pipeline
        
        # Execute pipeline with live progress tracking across all sub-steps
        package = run_cosmos_short_pipeline(
            custom_topic=topic_data,
            auto_upload=False, # strictly false for safety
            custom_position=subtitle_pos,
            theme_color_override=theme_color,
            preferred_model=preferred_model,
            progress_callback=on_progress
        )
        
        video_path = package.get("files", {}).get("video", "")
        thumb_path = package.get("files", {}).get("thumbnail_png", "")
        output_dir = os.path.dirname(video_path) if video_path else ""

        update_job(
            job_id,
            status="completed",
            progress_pct=100,
            current_step="Short & thumbnail ready for review / scheduling",
            video_path=video_path,
            thumbnail_path=thumb_path,
            output_dir=output_dir
        )
        logger.info(f"Job {job_id} finished successfully: {video_path}")
    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {e}", exc_info=True)
        update_job(
            job_id,
            status="failed",
            error_message=str(e),
            current_step=f"Failed: {str(e)[:150]}"
        )

@router.post("/start")
def start_video_generation(req: StartVideoRequest, background_tasks: BackgroundTasks):
    job_id = f"cosmos_{uuid.uuid4().hex[:10]}"
    
    # Auto-resolve category theme if not explicitly provided
    theme_color = req.theme_color
    subtitle_pos = req.subtitle_position_y or 76.0
    try:
        from backend.database import get_category_by_id, get_category_by_name
        cat = None
        if req.category_id:
            cat = get_category_by_id(req.category_id)
        if not cat and req.category:
            cat = get_category_by_name(req.category)
        if cat:
            if not theme_color:
                theme_color = cat.get("accent_color")
            if cat.get("caption_position_y"):
                subtitle_pos = float(cat["caption_position_y"])
    except Exception:
        pass

    topic_data = {
        "id": req.draft_id or f"t_{uuid.uuid4().hex[:6]}",
        "mode": req.mode,
        "title": req.title,
        "category": req.category,
        "script": req.hindi_script,
        "keywords": req.keywords,
        "language": req.language or "hindi",
        "topic": req.title
    }

    create_job(job_id, req.draft_id, params=topic_data)

    # Start in daemon thread so it continues smoothly
    t = threading.Thread(
        target=run_pipeline_thread,
        args=(job_id, topic_data, theme_color, subtitle_pos, req.preferred_model),
        daemon=True
    )
    t.start()

    return {
        "status": "started",
        "job_id": job_id,
        "message": "Video generation pipeline launched in background."
    }

@router.get("/active")
def get_active_pipeline_status():
    jobs = get_jobs(limit=15)
    active = next((j for j in jobs if j.get("status") in ["processing", "queued"]), None)
    latest_completed = next((j for j in jobs if j.get("status") == "completed"), None)
    return {
        "active_job": active,
        "latest_completed": latest_completed,
        "total_jobs": len(jobs)
    }

@router.post("/retry/{job_id}")
def retry_failed_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    params_data = None
    if job.get("params_json"):
        try:
            params_data = json.loads(job["params_json"])
        except Exception:
            pass

    if not params_data:
        from backend.database import get_drafts
        drafts = get_drafts(limit=5)
        draft = next((d for d in drafts if d.get("id") == job.get("draft_id")), None) if job.get("draft_id") else None
        params_data = {
            "id": job.get("draft_id") or f"retry_{job_id[-6:]}",
            "title": draft.get("title") if draft else "COSMOS Short",
            "category": draft.get("category") if draft else "Space & Universe",
            "script": draft.get("hindi_script") if draft else "",
            "keywords": draft.get("keywords") if draft else [],
            "language": "hindi",
            "mode": "story"
        }

    update_job(
        job_id,
        status="processing",
        progress_pct=10,
        current_step="Retrying render pipeline...",
        error_message=None
    )

    t = threading.Thread(
        target=run_pipeline_thread,
        args=(job_id, params_data, None, 76.0, "qwen2.5:3b"),
        daemon=True
    )
    t.start()

    return {"status": "retrying", "job_id": job_id, "message": "Job retry launched."}

@router.delete("/job/{job_id}")
def dismiss_job(job_id: str):
    from backend.database import delete_job
    delete_job(job_id)
    return {"status": "deleted", "job_id": job_id}

@router.get("/jobs")
def list_jobs(limit: int = 25):
    jobs = get_jobs(limit=limit)
    return {"jobs": jobs}

@router.get("/status/{job_id}")
def check_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/stream/{job_id}")
def stream_video(job_id: str):
    job = get_job(job_id)
    if not job or not job.get("video_path"):
        raise HTTPException(status_code=404, detail="Video file not found for this job")
    
    video_path = Path(job["video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"File {video_path.name} does not exist on disk")
    
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=video_path.name
    )

@router.get("/thumbnail/{job_id}")
def get_thumbnail(job_id: str):
    job = get_job(job_id)
    if not job or not job.get("thumbnail_path"):
        raise HTTPException(status_code=404, detail="Thumbnail not found for this job")
    
    thumb_path = Path(job["thumbnail_path"])
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file missing on disk")
    
    media_type = "image/png" if thumb_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(str(thumb_path), media_type=media_type)
