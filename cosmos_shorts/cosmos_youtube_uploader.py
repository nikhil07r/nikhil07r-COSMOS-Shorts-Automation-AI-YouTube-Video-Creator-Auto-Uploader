import os
import sys
import json
import time
from typing import Optional, Dict, Any

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def get_youtube_service(client_secrets_path: str, token_path: str):
    """
    Authenticates via OAuth 2.0 flow and returns the YouTube API service.
    """
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(
                    f"\n[!] Google OAuth client secret file not found at: {client_secrets_path}\n"
                    "Please download your client_secret.json from Google Cloud Console and place it here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")

        # Save credentials locally
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_cosmos_short(
    youtube,
    video_path: str,
    title: str,
    description: str,
    tags: list,
    thumbnail_path: Optional[str] = None,
    privacy_status: str = "private",
    publish_at: Optional[str] = None,
    category_id: str = "28"
) -> Dict[str, Any]:
    """
    Uploads a video to YouTube with resumable chunks, thumbnail, and metadata.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    if publish_at:
        # Scheduled publishing requires privacyStatus = "private"
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at

    print(f"\n[YouTube Upload] Starting upload for: {title}")
    print(f"Privacy Status: {body['status']['privacyStatus']}")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 2,  # 2MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retry_count = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        except Exception as e:
            retry_count += 1
            if retry_count > 5:
                raise e
            print(f"Upload interrupted, retrying in 5 seconds... ({e})")
            time.sleep(5)

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print(f"SUCCESS: Video uploaded successfully! Video ID: {video_id}")
    print(f"Watch URL: {video_url}")

    # Set custom thumbnail if provided
    thumbnail_set = False
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            print("Uploading custom thumbnail...")
            thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=thumb_media
            ).execute()
            thumbnail_set = True
            print("Thumbnail uploaded successfully!")
        except Exception as te:
            print(f"Notice: Thumbnail upload skipped or not permitted by channel tier: {te}")

    return {
        "success": True,
        "video_id": video_id,
        "video_url": video_url,
        "privacy_status": body["status"]["privacyStatus"],
        "publish_at": publish_at,
        "thumbnail_set": thumbnail_set
    }
