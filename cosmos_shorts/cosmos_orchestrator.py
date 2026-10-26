import os
import sys
import json
import time
import uuid
import shutil
import re
import math
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# Force UTF-8 encoding on Windows console
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Ensure MoneyPrinterTurbo is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MPT_DIR = os.path.join(BASE_DIR, "MoneyPrinterTurbo")
if MPT_DIR not in sys.path:
    sys.path.insert(0, MPT_DIR)

from app.models.schema import VideoParams
from app.services import task as mpt_task
from app.config import config as mpt_config

import cosmos_generator
import cosmos_thumbnail_builder
import cosmos_youtube_uploader

COSMOS_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(COSMOS_DIR, "cosmos_config.toml")
TOPICS_PATH = os.path.join(COSMOS_DIR, "cosmos_topics.json")
HISTORY_PATH = os.path.join(COSMOS_DIR, "cosmos_history.json")
OUTPUT_DIR = os.path.join(COSMOS_DIR, "output")
FFMPEG_EXE = os.path.join(BASE_DIR, "lib", "ffmpeg", "ffmpeg-7.0-essentials_build", "ffmpeg.exe")

# Theme color presets matching video categories
THEME_PRESETS = {
    "Space": {"bg": "#00E5FF", "text": "#000000", "label": "Electric Cyan"},
    "Dangerous Places": {"bg": "#FF2A55", "text": "#FFFFFF", "label": "Crimson Fire"},
    "Science & Nature": {"bg": "#00FF66", "text": "#000000", "label": "Neon Emerald"},
    "Deep Ocean": {"bg": "#00D2FF", "text": "#000000", "label": "Ocean Aqua"},
    "Human History": {"bg": "#FFB800", "text": "#000000", "label": "Ancient Gold"},
    "Strange Places": {"bg": "#FF3366", "text": "#FFFFFF", "label": "Vivid Coral"},
    "General": {"bg": "#00FF66", "text": "#000000", "label": "Neon Emerald"}
}

def resolve_theme(category: str, color_override: Optional[str] = None) -> Dict[str, str]:
    if color_override and color_override.startswith("#"):
        c = color_override.lstrip('#')
        if len(c) == 6:
            r, g, b = (int(c[i:i+2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b)
            text_color = "#000000" if luminance > 140 else "#FFFFFF"
            return {"bg": color_override, "text": text_color, "label": "Custom"}
            
    # Check SQLite database for custom category theme
    try:
        db_path = os.path.join(BASE_DIR, "cosmos_growth_os", "data", "cosmos_growth_os.db")
        if os.path.exists(db_path):
            import sqlite3
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT accent_color, text_color, theme_label FROM categories WHERE LOWER(name) = LOWER(?)", (category,))
            row = c.fetchone()
            conn.close()
            if row:
                return {"bg": row[0], "text": row[1], "label": row[2] or category}
    except Exception:
        pass

    return THEME_PRESETS.get(category, THEME_PRESETS.get("General", {"bg": "#8B5CF6", "text": "#FFFFFF", "label": "Electric Violet"}))

def load_json(path: str, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else []
    return default if default is not None else []

def save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_topic() -> Dict[str, Any]:
    topics = load_json(TOPICS_PATH, [])
    history = load_json(HISTORY_PATH, [])
    used_ids = {h.get("topic_id") for h in history if h.get("topic_id")}

    for t in topics:
        if t.get("id") not in used_ids:
            return t

    # If all used, recycle the first one
    return topics[0] if topics else {
        "id": "custom_default",
        "category": "Science & Nature",
        "topic_en": "Mysteries of the Universe",
        "topic_hi": "ब्रह्मांड के सबसे बड़े रहस्य"
    }

def get_video_duration(video_path: str) -> float:
    cmd = [
        FFMPEG_EXE, "-i", video_path
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    for line in proc.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0

def run_cosmos_short_pipeline(
    custom_topic: Optional[Dict[str, Any]] = None,
    auto_upload: bool = False,
    subtitle_position: str = "custom",
    custom_position: float = 76.0,
    theme_color_override: Optional[str] = None,
    preferred_model: Optional[str] = None,
    progress_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes the complete COSMOS Shorts creation pipeline:
    Topic/Story/Script -> Ollama/LLM -> Video (MPT) -> Thumbnail (PIL) -> QA Checks -> Storage -> Upload (Optional)
    """
    job_id = f"cosmos_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    print(f"\n==================================================")
    print(f"🚀 COSMOS AUTOMATED SHORTS CREATOR — Job: {job_id}")
    print(f"==================================================")

    # 1. Select Topic
    if progress_callback:
        progress_callback(15, "Initializing topic & category settings")
    topic = custom_topic if custom_topic else get_next_topic()
    category = topic.get("category", "General")
    theme = resolve_theme(category, theme_color_override)

    print(f"[Step 1] Input Mode: {topic.get('mode', 'topic')} | Category: {category}")
    print(f"         Theme Color: {theme.get('label')} (Badge: {theme['bg']}, Text: {theme['text']})")
    print(f"         Caption Position: {subtitle_position} (Y: {custom_position}%)")

    # 2. Generate Content with Local Ollama
    if progress_callback:
        progress_callback(30, f"Generating script with local AI ({preferred_model or 'Qwen'})...")
    print(f"[Step 2] Processing Story/Script with Ollama (Model: {preferred_model or 'default'})...")
    content = cosmos_generator.generate_cosmos_content(topic, preferred_model=preferred_model)
    print(f"  Title: {content.get('title')}")
    print(f"  Keywords: {content.get('keywords')}")

    # Calculate optimal clip duration to guarantee exact 1-to-1 sync and avoid round-robin clip repetition
    keywords = content.get("keywords", [])
    script_words = len(content.get("script", "").split())
    est_duration = max(35.0, script_words / 2.16)
    if keywords:
        optimal_clip_duration = max(5, int(math.ceil(est_duration / len(keywords))))
    else:
        optimal_clip_duration = 6
    print(f"  Pacing: Est Audio={est_duration:.1f}s | Keywords={len(keywords)} | Clip Duration={optimal_clip_duration}s")

    # 3. Create Video with MoneyPrinterTurbo
    if progress_callback:
        progress_callback(50, "Synthesizing voiceover & downloading HD video clips...")
    print(f"[Step 3] Rendering Video via MoneyPrinterTurbo Pipeline...")
    task_id = str(uuid.uuid4())
    params = VideoParams(
        video_subject=content.get("title", "COSMOS Short"),
        video_script=content.get("script", ""),
        video_terms=",".join(keywords),
        video_aspect="9:16",
        video_source="pixabay",
        voice_name="hi-IN-MadhurNeural-Male",
        font_name="Nirmala.ttc",
        subtitle_enabled=True,
        subtitle_position=subtitle_position,
        custom_position=custom_position,
        subtitle_display_mode="word_by_word",
        subtitle_animation="pop_spring",
        text_fore_color=theme["text"],
        text_background_color=theme["bg"],
        rounded_subtitle_background=True,
        font_size=70,
        stroke_color="#000000",
        stroke_width=2.0,
        match_materials_to_script=True,
        video_concat_mode="sequential",
        video_transition_mode=None,
        bgm_type="random",
        bgm_volume=0.15,
        video_clip_duration=optimal_clip_duration,
        video_clip_speed=1.0,
        video_count=1
    )

    if progress_callback:
        progress_callback(70, "Assembling 1080x1920 MP4 & dynamic animated subtitles...")
    result = mpt_task.start(task_id, params, stop_at="video")
    if not result or not result.get("videos"):
        raise RuntimeError("MoneyPrinterTurbo video generation failed to produce output.")

    raw_video_path = result["videos"][0]
    final_video_path = os.path.join(job_dir, "video.mp4")
    shutil.copy2(raw_video_path, final_video_path)
    print(f"  Video rendered successfully: {final_video_path}")

    # 4. Extract Clean Thumbnail Frame & Generate Thumbnail
    if progress_callback:
        progress_callback(85, "Creating high-contrast 1080x1920 viral thumbnail badge...")
    print(f"[Step 4] Creating Custom COSMOS 1080x1920 Thumbnail...")
    frame_path = os.path.join(job_dir, "frame_preview.png")
    clean_source = final_video_path
    if result.get("combined_videos") and os.path.exists(result["combined_videos"][0]):
        clean_source = result["combined_videos"][0]

    duration = get_video_duration(final_video_path)
    sample_time = "00:00:03" if duration >= 6.0 else "00:00:01"
    subprocess.run([
        FFMPEG_EXE, "-ss", sample_time, "-i", clean_source,
        "-vframes", "1", "-q:v", "2", frame_path, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    thumb_png = os.path.join(job_dir, "thumbnail.png")
    thumb_jpg = os.path.join(job_dir, "thumbnail.jpg")
    clean_title = re.sub(r'[\U00010000-\U0010ffff]|#\w+', '', content.get("title", "COSMOS Short")).strip()
    clean_title = clean_title.replace("!", "").strip()
    if not clean_title:
        clean_title = topic.get("topic_hi", "COSMOS Short")

    cosmos_thumbnail_builder.create_cosmos_thumbnail(
        bg_image_path=frame_path if os.path.exists(frame_path) else None,
        output_path=thumb_png,
        headline_hi=clean_title,
        subtext=content.get("thumbnail_text", "क्या ये सच में है?!"),
        badge_color_hex=theme["bg"],
        badge_text_color_hex=theme["text"]
    )
    print(f"  Thumbnail created: {thumb_png}")

    # 5. Quality Assurance Checks
    if progress_callback:
        progress_callback(95, "Running final quality & duration verification...")
    print(f"[Step 5] Running Pre-Upload Quality Checks...")
    qa_results = {
        "video_exists": os.path.exists(final_video_path),
        "video_size_bytes": os.path.getsize(final_video_path),
        "duration_seconds": duration,
        "duration_valid": 35.0 <= duration <= 65.0,
        "thumbnail_exists": os.path.exists(thumb_jpg),
        "thumbnail_size_bytes": os.path.getsize(thumb_jpg) if os.path.exists(thumb_jpg) else 0,
        "all_passed": False
    }
    qa_results["all_passed"] = (
        qa_results["video_exists"]
        and qa_results["video_size_bytes"] > 500000
        and qa_results["duration_valid"]
        and qa_results["thumbnail_exists"]
    )
    print(f"  QA Passed: {qa_results['all_passed']} (Duration: {duration:.1f}s, Size: {qa_results['video_size_bytes'] / (1024*1024):.1f} MB)")

    # 6. Save Metadata and Package
    meta_path = os.path.join(job_dir, "metadata.json")
    package = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(),
        "topic": topic,
        "theme": theme,
        "subtitle_settings": {
            "position": subtitle_position,
            "custom_y_percent": custom_position,
            "badge_color": theme["bg"],
            "text_color": theme["text"]
        },
        "content": content,
        "files": {
            "video": final_video_path,
            "thumbnail_png": thumb_png,
            "thumbnail_jpg": thumb_jpg,
            "preview_frame": frame_path
        },
        "qa_checks": qa_results,
        "upload_status": "PENDING"
    }
    save_json(meta_path, package)

    # 7. Update History
    history = load_json(HISTORY_PATH, [])
    history.append({
        "job_id": job_id,
        "topic_id": topic.get("id"),
        "title": content.get("title"),
        "created_at": datetime.now().isoformat(),
        "duration": duration,
        "output_dir": job_dir
    })
    save_json(HISTORY_PATH, history)

    # 8. YouTube Upload (If auto_upload requested and credentials present)
    client_secrets = os.path.join(COSMOS_DIR, "client_secret.json")
    token_file = os.path.join(COSMOS_DIR, "token.json")
    if auto_upload:
        if os.path.exists(client_secrets) or os.path.exists(token_file):
            print(f"[Step 6] Authenticating and uploading to YouTube (PRIVATE)...")
            try:
                youtube = cosmos_youtube_uploader.get_youtube_service(client_secrets, token_file)
                upload_res = cosmos_youtube_uploader.upload_cosmos_short(
                    youtube=youtube,
                    video_path=final_video_path,
                    title=content.get("title"),
                    description=content.get("description", "") + "\n\n#shorts #cosmos #facts #hindi",
                    tags=content.get("tags", ["COSMOS", "Shorts"]),
                    thumbnail_path=thumb_jpg,
                    privacy_status="private"
                )
                package["upload_status"] = "UPLOADED_PRIVATE"
                package["youtube_details"] = upload_res
                save_json(meta_path, package)
                print(f"  YouTube Upload Completed! URL: {upload_res.get('video_url')}")
            except Exception as ue:
                print(f"  YouTube Upload Notice: {ue}")
                package["upload_status"] = f"FAILED: {ue}"
                save_json(meta_path, package)
        else:
            print(f"[Notice] YouTube OAuth credentials not yet placed at: {client_secrets}")
            print(f"         Video and Thumbnail are saved locally and ready for upload!")

    print(f"\n==================================================")
    print(f"✅ JOB COMPLETE! Assets saved to:")
    print(f"   {job_dir}")
    print(f"==================================================\n")

    return package

if __name__ == "__main__":
    run_cosmos_short_pipeline()
