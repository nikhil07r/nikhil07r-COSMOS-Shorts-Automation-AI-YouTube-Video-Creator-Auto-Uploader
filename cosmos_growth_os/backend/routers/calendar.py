import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.config import TOKEN_FILE, CLIENT_SECRET_FILE
from backend.database import get_calendar_events, add_calendar_event, get_connection
from backend.routers.youtube import get_youtube_service

router = APIRouter(prefix="/api/calendar", tags=["calendar"])
logger = logging.getLogger("cosmos.calendar")

class ScheduleRequest(BaseModel):
    draft_id: Optional[str] = None
    video_path: str
    thumbnail_path: Optional[str] = None
    title: str
    scheduled_for: str # ISO string or YYYY-MM-DD HH:MM
    privacy_status: Optional[str] = "private"
    upload_to_youtube_now: Optional[bool] = False

class UploadNowRequest(BaseModel):
    event_id: Optional[str] = None
    video_path: str
    thumbnail_path: Optional[str] = None
    title: str
    description: Optional[str] = ""
    tags: Optional[List[str]] = ["#Shorts", "#COSMOS", "#SpaceMysteries", "#FactsInHindi"]
    privacy_status: Optional[str] = "private"
    publish_at: Optional[str] = None # RFC 3339 formatted UTC timestamp for YouTube scheduling
    confirmed_public: Optional[bool] = False # Explicit confirmation gate

@router.get("/best_time_slot")
def get_best_time_slot():
    """Computes the next optimal algorithmic release window for Hindi Shorts (18:30 IST)."""
    now = datetime.now()
    today_target = now.replace(hour=18, minute=30, second=0, microsecond=0)
    
    # If less than 15 mins left before 18:30 or already past, schedule for tomorrow 18:30
    if now >= today_target - timedelta(minutes=15):
        target_dt = today_target + timedelta(days=1)
        day_word = "Tomorrow"
    else:
        target_dt = today_target
        day_word = "Today"

    d_str = target_dt.strftime("%d %b")
    label = f"{day_word} at 18:30 IST ({d_str})"
    local_iso = target_dt.strftime("%Y-%m-%dT%H:%M")
    
    # Convert IST to UTC RFC3339 for YouTube Data API
    utc_dt = target_dt - timedelta(hours=5, minutes=30)
    rfc3339 = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "target_local_iso": local_iso,
        "target_utc_rfc3339": rfc3339,
        "label": label,
        "hour_window": "18:00 – 21:00 IST",
        "audience": "Peak Hindi educational viewer retention"
    }

@router.get("/events")
def list_events():
    events = get_calendar_events()
    return {"events": events}

@router.post("/schedule")
def schedule_video(req: ScheduleRequest):
    event_id = f"ev_{uuid.uuid4().hex[:8]}"
    event_data = {
        "id": event_id,
        "draft_id": req.draft_id,
        "video_path": req.video_path,
        "title": req.title,
        "scheduled_for": req.scheduled_for,
        "privacy_status": req.privacy_status or "private",
        "upload_status": "pending"
    }
    add_calendar_event(event_data)
    return {"status": "scheduled", "event": event_data}

@router.post("/upload")
def upload_video_now(req: UploadNowRequest):
    # Safety Check: Never upload publicly without explicit confirmation
    if req.privacy_status == "public" and not req.confirmed_public:
        raise HTTPException(
            status_code=400,
            detail="Public upload safety gate triggered: You must explicitly confirm public publishing. Recommended: Upload as 'private' first to review on YouTube Studio."
        )

    try:
        yt = get_youtube_service()
        from cosmos_youtube_uploader import upload_cosmos_short
        
        desc = req.description or f"{req.title}\n\nExplore the deepest mysteries of the universe with COSMOS VIRAL.\nSubscribe for daily mind-bending space facts and science mysteries!\n\n#Shorts #COSMOS #SpaceFacts #HindiFacts #Science"
        
        result = upload_cosmos_short(
            youtube=yt,
            video_path=req.video_path,
            title=req.title,
            description=desc,
            tags=req.tags or ["Shorts", "COSMOS", "Facts"],
            thumbnail_path=req.thumbnail_path,
            privacy_status=req.privacy_status or "private",
            publish_at=req.publish_at
        )
        
        video_id = result.get("video_id")
        
        # If associated with calendar event, update it
        status_label = "scheduled_on_youtube" if req.publish_at else "uploaded"
        if req.event_id:
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
            UPDATE calendar_events 
            SET upload_status = ?, youtube_video_id = ?, published_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (status_label, video_id, req.event_id))
            conn.commit()
            conn.close()

        msg = f"Successfully uploaded video and scheduled it for {req.publish_at} on YouTube!" if req.publish_at else f"Successfully uploaded video as {req.privacy_status.upper()} to channel COSMOS VIRAL!"

        return {
            "status": "success",
            "video_id": video_id,
            "privacy_status": req.privacy_status,
            "publish_at": req.publish_at,
            "youtube_url": f"https://youtube.com/shorts/{video_id}" if video_id else None,
            "message": msg
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
