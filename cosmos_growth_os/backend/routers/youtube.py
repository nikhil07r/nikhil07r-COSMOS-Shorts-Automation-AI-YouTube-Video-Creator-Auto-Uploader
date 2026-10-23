import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
import google.oauth2.credentials
from googleapiclient.discovery import build
from backend.config import TOKEN_FILE, CLIENT_SECRET_FILE
from backend.database import upsert_channel, get_channel, upsert_videos, get_videos
from backend.security import redact_sensitive_data

router = APIRouter(prefix="/api/youtube", tags=["youtube"])
logger = logging.getLogger("cosmos.youtube")

def get_youtube_service():
    if not TOKEN_FILE.exists():
        raise HTTPException(status_code=401, detail="YouTube token.json not found. Please authenticate your channel.")
    
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token_data = json.load(f)
    
    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(token_data)
    # Rebuild service
    return build("youtube", "v3", credentials=creds)

@router.get("/status")
def youtube_status():
    token_exists = TOKEN_FILE.exists()
    client_secret_exists = CLIENT_SECRET_FILE.exists()
    cached_channel = get_channel()
    
    return {
        "authenticated": token_exists,
        "client_secret_configured": client_secret_exists,
        "channel": cached_channel,
        "token_file": str(TOKEN_FILE)
    }

@router.post("/sync")
def sync_channel_data():
    """Fetches real-time channel statistics and latest videos from YouTube API."""
    try:
        yt = get_youtube_service()
        # 1. Fetch channel details
        res = yt.channels().list(mine=True, part="snippet,statistics,contentDetails").execute()
        items = res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No YouTube channel found for authenticated account.")
        
        ch_item = items[0]
        channel_id = ch_item["id"]
        snippet = ch_item["snippet"]
        stats = ch_item["statistics"]
        
        channel_data = {
            "channel_id": channel_id,
            "title": snippet.get("title", "COSMOS VIRAL"),
            "custom_url": snippet.get("customUrl", "@cosmos-1nr"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0))
        }
        upsert_channel(channel_data)

        # 2. Fetch latest uploads playlist
        uploads_playlist_id = ch_item["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist_res = yt.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet,contentDetails",
            maxResults=50
        ).execute()

        video_ids = [item["contentDetails"]["videoId"] for item in playlist_res.get("items", [])]
        
        # 3. Fetch detailed statistics for those videos
        synced_videos = []
        if video_ids:
            videos_res = yt.videos().list(
                id=",".join(video_ids),
                part="snippet,contentDetails,statistics"
            ).execute()
            
            for v in videos_res.get("items", []):
                v_snip = v["snippet"]
                v_stat = v.get("statistics", {})
                v_content = v.get("contentDetails", {})
                
                # Check duration (Shorts are typically <= 60 seconds)
                duration_str = v_content.get("duration", "PT0S")
                # Parse simple ISO duration
                duration_seconds = 60 # default
                try:
                    import re
                    match = re.search(r'PT(?:(\d+)M)?(?:(\d+)S)?', duration_str)
                    if match:
                        m = int(match.group(1) or 0)
                        s = int(match.group(2) or 0)
                        duration_seconds = m * 60 + s
                except Exception:
                    pass

                synced_videos.append({
                    "video_id": v["id"],
                    "channel_id": channel_id,
                    "title": v_snip.get("title", ""),
                    "description": v_snip.get("description", "")[:200],
                    "published_at": v_snip.get("publishedAt"),
                    "thumbnail_url": v_snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
                    "view_count": int(v_stat.get("viewCount", 0)),
                    "like_count": int(v_stat.get("likeCount", 0)),
                    "comment_count": int(v_stat.get("commentCount", 0)),
                    "duration_seconds": duration_seconds,
                    "is_short": duration_seconds <= 60
                })
            
            upsert_videos(synced_videos)

        return {
            "status": "success",
            "channel": channel_data,
            "synced_videos_count": len(synced_videos),
            "message": f"Successfully synced {len(synced_videos)} videos for {channel_data['title']}."
        }
    except Exception as e:
        logger.error(f"YouTube sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos")
def list_videos(limit: int = 50, is_short: Optional[bool] = None):
    videos = get_videos(limit=limit, is_short=is_short)
    return {"videos": videos, "total": len(videos)}
