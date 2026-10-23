import sqlite3
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

logger = logging.getLogger("cosmos.db")

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Automatically initialize tables on import if they don't exist
def ensure_initialized():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
    if not c.fetchone():
        init_db()
    conn.close()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        channel_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        custom_url TEXT,
        thumbnail_url TEXT,
        subscriber_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        video_count INTEGER DEFAULT 0,
        last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        channel_id TEXT,
        title TEXT NOT NULL,
        description TEXT,
        published_at TIMESTAMP,
        thumbnail_url TEXT,
        view_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        duration_seconds INTEGER DEFAULT 0,
        is_short BOOLEAN DEFAULT 1,
        FOREIGN KEY(channel_id) REFERENCES channels(channel_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content_drafts (
        id TEXT PRIMARY KEY,
        mode TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        hindi_script TEXT NOT NULL,
        english_script TEXT,
        keywords_json TEXT,
        facts_checklist_json TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        draft_id TEXT,
        status TEXT DEFAULT 'queued',
        progress_pct INTEGER DEFAULT 0,
        current_step TEXT,
        error_message TEXT,
        output_dir TEXT,
        video_path TEXT,
        thumbnail_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY,
        draft_id TEXT,
        video_path TEXT,
        title TEXT NOT NULL,
        scheduled_for TIMESTAMP NOT NULL,
        privacy_status TEXT DEFAULT 'private',
        upload_status TEXT DEFAULT 'pending',
        youtube_video_id TEXT,
        published_at TIMESTAMP,
        FOREIGN KEY(draft_id) REFERENCES content_drafts(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        accent_color TEXT NOT NULL,
        text_color TEXT NOT NULL,
        icon TEXT DEFAULT '🪐',
        theme_label TEXT,
        visual_style TEXT DEFAULT 'Cinematic Drone',
        default_language TEXT DEFAULT 'hindi',
        default_duration INTEGER DEFAULT 52,
        caption_position_y REAL DEFAULT 76.0,
        caption_font_size INTEGER DEFAULT 70,
        caption_highlight_color TEXT,
        prompt_template_id TEXT,
        custom_prompt_instructions TEXT,
        is_default INTEGER DEFAULT 0,
        is_enabled INTEGER DEFAULT 1,
        order_index INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Prompt Templates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_templates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category_id TEXT,
        language TEXT DEFAULT 'hindi',
        system_prompt TEXT,
        user_prompt_template TEXT,
        is_global INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Default Categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_cats = [
            ("cat_space_universe", "Space & Universe", "Deep cosmic wonders, black holes, rogue planets, and stellar events.", "#00E5FF", "#000000", "🪐", "Electric Cyan", "Cinematic Deep Space & Telescopic CG", "hindi", 52, 76.0, 70, "#00E5FF", "tpl_viral_mystery_hi", "Focus on cosmic mystery, awe, scale, and mind-bending physics facts with dramatic pacing.", 1, 1, 0),
            ("cat_earth_mysteries", "Earth Mysteries", "Strange subterranean formations, Bermuda triangle, ancient geological anomalies.", "#10B981", "#000000", "🌍", "Neon Emerald", "Drone Landscape & Nature Explorations", "hindi", 52, 76.0, 70, "#10B981", "tpl_viral_mystery_hi", "Emphasize unsolved planetary phenomena, eyewitness lore, and scientific hypotheses.", 0, 1, 1),
            ("cat_dangerous_places", "Dangerous Places", "Extreme death zones, volcanic cauldrons, toxic islands, and forbidden territories.", "#FF2A55", "#FFFFFF", "🌋", "Crimson Fire", "High Tension & Dark Atmosphere", "hindi", 50, 76.0, 70, "#FF2A55", "tpl_viral_mystery_hi", "Use high-adrenaline suspense hook, explain survival hazards, and state why entry is banned.", 0, 1, 2),
            ("cat_human_history", "Human History", "Lost civilizations, megalithic architecture, bizarre royal secrets, and forgotten empires.", "#FFB800", "#000000", "🏛️", "Ancient Gold", "Archival & Monumental Scenery", "hindi", 54, 76.0, 70, "#FFB800", "tpl_viral_mystery_hi", "Connect ancient feats with modern archaeological puzzles. Contrast past knowledge with modern theories.", 0, 1, 3),
            ("cat_science_anomalies", "Science Anomalies", "Quantum paradoxes, unexplainable physics experiments, and time dilation.", "#8B5CF6", "#FFFFFF", "⚡", "Electric Violet", "Futuristic Cyberpunk & Scientific Lab", "hindi", 52, 76.0, 70, "#8B5CF6", "tpl_viral_mystery_hi", "Explain complex counter-intuitive scientific paradoxes in simple relatable analogies.", 0, 1, 4),
            ("cat_business_finance", "Business & Finance", "Billionaire moves, corporate blunders, money psychology, and market secrets.", "#06B6D4", "#000000", "💼", "Venture Cyan", "Modern Corporate & Stock Charts", "hinglish", 50, 76.0, 70, "#06B6D4", "tpl_business_breakdown", "Use conversational Roman Hinglish (e.g. 'Dosto, kya aap jaante hain...'). Explain financial concepts simply. Avoid unverified claims or guaranteed profit promises.", 0, 1, 5),
            ("cat_tech_ai", "Technology & AI", "Breakthrough AI models, humanoid robotics, quantum chips, and future tech.", "#3B82F6", "#FFFFFF", "🤖", "Neural Cobalt", "Futuristic Sci-Fi & Clean Tech", "hinglish", 50, 76.0, 70, "#3B82F6", "tpl_hinglish_conversational", "Focus on AI advancements, practical implications, and ethical dilemmas in punchy Hinglish.", 0, 1, 6)
        ]
        cursor.executemany("""
        INSERT INTO categories (id, name, description, accent_color, text_color, icon, theme_label, visual_style, default_language, default_duration, caption_position_y, caption_font_size, caption_highlight_color, prompt_template_id, custom_prompt_instructions, is_default, is_enabled, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_cats)

    # Seed Default Prompt Templates if empty
    cursor.execute("SELECT COUNT(*) FROM prompt_templates")
    if cursor.fetchone()[0] == 0:
        default_templates = [
            ("tpl_viral_mystery_hi", "Standard Mystery & Suspense (Hindi)", "Classic COSMOS formula: 3s hook, escalating suspense, 4 verified facts, outro.", None, "hindi", 
             "You are the Lead Scriptwriter for COSMOS VIRAL. Create high-retention Hindi educational Shorts with 0-3s suspense hook, 3-4 mind-bending facts, and punchline outro in Devanagari script.",
             "Create a viral Hindi Short concept from this prompt:\nConcept: {prompt}\nCategory: {category}\nAdditional Instructions: {extra_instructions}\nLanguage: Pure Hindi in Devanagari script.\nEnsure 5-7 English stock video keywords sequential matching each scene.", 1),
            ("tpl_hinglish_conversational", "Conversational Hinglish (Roman Script)", "Modern YouTube youth style: Roman Hinglish narration, relatable tone, dynamic hooks.", None, "hinglish",
             "You are the Lead Scriptwriter for COSMOS VIRAL. Create high-retention conversational Hinglish Shorts using ROMAN SCRIPT (English alphabet, e.g. 'Dosto, kya aap jaante hain...'). Do NOT output Devanagari script.",
             "Create a viral Hinglish Short concept from this prompt:\nConcept: {prompt}\nCategory: {category}\nAdditional Instructions: {extra_instructions}\nLanguage: Natural Roman-script Hinglish (English alphabet only).\nEnsure 5-7 English stock video keywords matching scenes in order.", 1),
            ("tpl_business_breakdown", "Business & Finance Breakdown (Hinglish)", "Financial insights, real company examples, no unverified profit claims, Roman script.", "cat_business_finance", "hinglish",
             "You are a Senior Financial Content Strategist. Create a fast-paced, insightful 45-55 second Short explaining a business move or financial insight in Roman Hinglish. Avoid unverified profit guarantees.",
             "Create an educational Business Short:\nConcept: {prompt}\nCategory: Business & Finance\nAdditional Instructions: {extra_instructions}\nLanguage: Roman-script Hinglish.\nEnsure 5-7 clean business stock footage keywords.", 0)
        ]
        cursor.executemany("""
        INSERT INTO prompt_templates (id, name, description, category_id, language, system_prompt, user_prompt_template, is_global)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_templates)

    # Default settings
    cursor.execute("""
    INSERT OR IGNORE INTO system_settings (key, value) VALUES 
        ('theme', 'dark'),
        ('ollama_model', 'qwen2.5:7b'),
        ('default_voice', 'hi-IN-MadhurNeural'),
        ('default_privacy', 'private'),
        ('auto_sync_interval_mins', '60');
    """)

    conn.commit()
    conn.close()
    logger.info("Database schema initialized.")

# Helper queries
def get_channel() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM channels ORDER BY last_synced_at DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_channel(ch: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO channels (channel_id, title, custom_url, thumbnail_url, subscriber_count, view_count, video_count, last_synced_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(channel_id) DO UPDATE SET
        title=excluded.title,
        custom_url=excluded.custom_url,
        thumbnail_url=excluded.thumbnail_url,
        subscriber_count=excluded.subscriber_count,
        view_count=excluded.view_count,
        video_count=excluded.video_count,
        last_synced_at=CURRENT_TIMESTAMP
    """, (
        ch.get("channel_id"),
        ch.get("title"),
        ch.get("custom_url"),
        ch.get("thumbnail_url"),
        ch.get("subscriber_count", 0),
        ch.get("view_count", 0),
        ch.get("video_count", 0)
    ))
    conn.commit()
    conn.close()

def upsert_videos(videos: List[Dict[str, Any]]):
    conn = get_connection()
    c = conn.cursor()
    for v in videos:
        c.execute("""
        INSERT INTO videos (video_id, channel_id, title, description, published_at, thumbnail_url, view_count, like_count, comment_count, duration_seconds, is_short)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(video_id) DO UPDATE SET
            title=excluded.title,
            description=excluded.description,
            published_at=excluded.published_at,
            thumbnail_url=excluded.thumbnail_url,
            view_count=excluded.view_count,
            like_count=excluded.like_count,
            comment_count=excluded.comment_count,
            duration_seconds=excluded.duration_seconds,
            is_short=excluded.is_short
        """, (
            v.get("video_id"),
            v.get("channel_id"),
            v.get("title"),
            v.get("description"),
            v.get("published_at"),
            v.get("thumbnail_url"),
            v.get("view_count", 0),
            v.get("like_count", 0),
            v.get("comment_count", 0),
            v.get("duration_seconds", 0),
            v.get("is_short", 1)
        ))
    conn.commit()
    conn.close()

def get_videos(limit: int = 50, is_short: Optional[bool] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    if is_short is not None:
        c.execute("SELECT * FROM videos WHERE is_short=? ORDER BY published_at DESC LIMIT ?", (1 if is_short else 0, limit))
    else:
        c.execute("SELECT * FROM videos ORDER BY published_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_setting(key: str, default: Any = None) -> Any:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM system_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: Any):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO system_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
    """, (key, str(value)))
    conn.commit()
    conn.close()

def save_draft(draft: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO content_drafts (id, mode, title, category, hindi_script, english_script, keywords_json, facts_checklist_json, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
        title=excluded.title,
        category=excluded.category,
        hindi_script=excluded.hindi_script,
        english_script=excluded.english_script,
        keywords_json=excluded.keywords_json,
        facts_checklist_json=excluded.facts_checklist_json,
        status=excluded.status,
        updated_at=CURRENT_TIMESTAMP
    """, (
        draft["id"],
        draft.get("mode", "story"),
        draft["title"],
        draft.get("category", "Mysteries"),
        draft["hindi_script"],
        draft.get("english_script", ""),
        json.dumps(draft.get("keywords", [])),
        json.dumps(draft.get("facts_checklist", [])),
        draft.get("status", "draft")
    ))
    conn.commit()
    conn.close()

def get_drafts(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM content_drafts ORDER BY updated_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["keywords"] = json.loads(d["keywords_json"]) if d.get("keywords_json") else []
        d["facts_checklist"] = json.loads(d["facts_checklist_json"]) if d.get("facts_checklist_json") else []
        result.append(d)
    return result

def create_job(job_id: str, draft_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO jobs (job_id, draft_id, status, progress_pct, current_step, created_at)
    VALUES (?, ?, 'queued', 0, 'Job initialized', CURRENT_TIMESTAMP)
    """, (job_id, draft_id))
    conn.commit()
    conn.close()
    return {"job_id": job_id, "status": "queued", "progress_pct": 0}

def update_job(job_id: str, **kwargs):
    conn = get_connection()
    c = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    if "status" in kwargs and kwargs["status"] in ["completed", "failed"]:
        fields.append("completed_at = CURRENT_TIMESTAMP")
    values.append(job_id)
    query = f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_calendar_events() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM calendar_events ORDER BY scheduled_for ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_calendar_event(event: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO calendar_events (id, draft_id, video_path, title, scheduled_for, privacy_status, upload_status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event["id"],
        event.get("draft_id"),
        event.get("video_path"),
        event["title"],
        event["scheduled_for"],
        event.get("privacy_status", "private"),
        event.get("upload_status", "pending")
    ))
    conn.commit()
    conn.close()

# ----------------------------------------------------
# CATEGORY MANAGEMENT CRUD
# ----------------------------------------------------
def get_categories(include_disabled: bool = False) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    if include_disabled:
        c.execute("SELECT * FROM categories ORDER BY order_index ASC, created_at ASC")
    else:
        c.execute("SELECT * FROM categories WHERE is_enabled = 1 ORDER BY order_index ASC, created_at ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_category_by_id(cat_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_category_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name.strip(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_category(data: Dict[str, Any]) -> Dict[str, Any]:
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Category name cannot be empty.")
    
    existing = get_category_by_name(name)
    if existing:
        raise ValueError(f"Category with name '{name}' already exists.")

    cat_id = data.get("id") or f"cat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}"
    
    accent_color = data.get("accent_color", "#8B5CF6")
    # Auto calculate text color if not provided
    text_color = data.get("text_color")
    if not text_color:
        hex_clean = accent_color.lstrip("#")
        if len(hex_clean) == 6:
            r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "#000000" if luminance > 0.55 else "#FFFFFF"
        else:
            text_color = "#FFFFFF"

    conn = get_connection()
    c = conn.cursor()
    
    # If is_default is set to 1, unset other defaults
    if data.get("is_default"):
        c.execute("UPDATE categories SET is_default = 0")

    c.execute("""
    INSERT INTO categories (
        id, name, description, accent_color, text_color, icon, theme_label, 
        visual_style, default_language, default_duration, caption_position_y, 
        caption_font_size, caption_highlight_color, prompt_template_id, 
        custom_prompt_instructions, is_default, is_enabled, order_index
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cat_id,
        name,
        data.get("description", ""),
        accent_color,
        text_color,
        data.get("icon", "🎯"),
        data.get("theme_label", name),
        data.get("visual_style", "Cinematic Drone"),
        data.get("default_language", "hindi"),
        data.get("default_duration", 52),
        data.get("caption_position_y", 76.0),
        data.get("caption_font_size", 70),
        data.get("caption_highlight_color", accent_color),
        data.get("prompt_template_id"),
        data.get("custom_prompt_instructions", ""),
        1 if data.get("is_default") else 0,
        1 if data.get("is_enabled", True) else 0,
        data.get("order_index", 99)
    ))
    conn.commit()
    conn.close()
    return get_category_by_id(cat_id)

def update_category(cat_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    cat = get_category_by_id(cat_id)
    if not cat:
        raise ValueError(f"Category '{cat_id}' not found.")

    new_name = data.get("name", cat["name"]).strip()
    if new_name.lower() != cat["name"].lower():
        existing = get_category_by_name(new_name)
        if existing and existing["id"] != cat_id:
            raise ValueError(f"Category name '{new_name}' already exists.")

    accent_color = data.get("accent_color", cat["accent_color"])
    text_color = data.get("text_color")
    if not text_color:
        hex_clean = accent_color.lstrip("#")
        if len(hex_clean) == 6:
            r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            text_color = "#000000" if luminance > 0.55 else "#FFFFFF"
        else:
            text_color = cat["text_color"]

    conn = get_connection()
    c = conn.cursor()
    
    if data.get("is_default"):
        c.execute("UPDATE categories SET is_default = 0")

    c.execute("""
    UPDATE categories SET
        name = ?,
        description = ?,
        accent_color = ?,
        text_color = ?,
        icon = ?,
        theme_label = ?,
        visual_style = ?,
        default_language = ?,
        default_duration = ?,
        caption_position_y = ?,
        caption_font_size = ?,
        caption_highlight_color = ?,
        prompt_template_id = ?,
        custom_prompt_instructions = ?,
        is_default = ?,
        is_enabled = ?,
        order_index = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        new_name,
        data.get("description", cat["description"]),
        accent_color,
        text_color,
        data.get("icon", cat["icon"]),
        data.get("theme_label", cat["theme_label"]),
        data.get("visual_style", cat["visual_style"]),
        data.get("default_language", cat["default_language"]),
        data.get("default_duration", cat["default_duration"]),
        data.get("caption_position_y", cat["caption_position_y"]),
        data.get("caption_font_size", cat["caption_font_size"]),
        data.get("caption_highlight_color", data.get("caption_highlight_color", accent_color)),
        data.get("prompt_template_id", cat["prompt_template_id"]),
        data.get("custom_prompt_instructions", cat["custom_prompt_instructions"]),
        1 if data.get("is_default", cat["is_default"]) else 0,
        1 if data.get("is_enabled", cat["is_enabled"]) else 0,
        data.get("order_index", cat["order_index"]),
        cat_id
    ))
    conn.commit()
    conn.close()
    return get_category_by_id(cat_id)

def delete_category(cat_id: str, reassign_to_id: Optional[str] = None, archive_only: bool = False) -> Dict[str, Any]:
    cat = get_category_by_id(cat_id)
    if not cat:
        raise ValueError(f"Category '{cat_id}' not found.")

    conn = get_connection()
    c = conn.cursor()
    
    # Check if category is used in drafts
    c.execute("SELECT COUNT(*) FROM content_drafts WHERE category = ?", (cat["name"],))
    drafts_count = c.fetchone()[0]

    if archive_only:
        c.execute("UPDATE categories SET is_enabled = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        return {"action": "archived", "id": cat_id, "name": cat["name"], "affected_drafts": drafts_count}

    if drafts_count > 0:
        if reassign_to_id:
            reassign_cat = get_category_by_id(reassign_to_id)
            if not reassign_cat:
                conn.close()
                raise ValueError(f"Reassignment target category '{reassign_to_id}' not found.")
            c.execute("UPDATE content_drafts SET category = ? WHERE category = ?", (reassign_cat["name"], cat["name"]))
        else:
            # Reassign to default or first available category
            c.execute("SELECT name FROM categories WHERE id != ? AND is_enabled = 1 ORDER BY is_default DESC LIMIT 1", (cat_id,))
            fallback = c.fetchone()
            fallback_name = fallback[0] if fallback else "General"
            c.execute("UPDATE content_drafts SET category = ? WHERE category = ?", (fallback_name, cat["name"]))

    c.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"action": "deleted", "id": cat_id, "name": cat["name"], "reassigned_drafts": drafts_count}

def duplicate_category(cat_id: str) -> Dict[str, Any]:
    cat = get_category_by_id(cat_id)
    if not cat:
        raise ValueError(f"Category '{cat_id}' not found.")

    # Find unique duplicate name
    base_name = f"{cat['name']} (Copy)"
    counter = 1
    new_name = base_name
    while get_category_by_name(new_name):
        counter += 1
        new_name = f"{cat['name']} (Copy {counter})"

    dup_data = dict(cat)
    dup_data.pop("id", None)
    dup_data.pop("created_at", None)
    dup_data.pop("updated_at", None)
    dup_data["name"] = new_name
    dup_data["is_default"] = 0
    return create_category(dup_data)

# ----------------------------------------------------
# PROMPT TEMPLATES CRUD
# ----------------------------------------------------
def get_prompt_templates(category_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    if category_id:
        c.execute("SELECT * FROM prompt_templates WHERE is_global = 1 OR category_id = ? ORDER BY name ASC", (category_id,))
    else:
        c.execute("SELECT * FROM prompt_templates ORDER BY is_global DESC, name ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_prompt_template_by_id(tpl_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM prompt_templates WHERE id = ?", (tpl_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_prompt_template(data: Dict[str, Any]) -> Dict[str, Any]:
    tpl_id = data.get("id") or f"tpl_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}"
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Template name cannot be empty.")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO prompt_templates (id, name, description, category_id, language, system_prompt, user_prompt_template, is_global)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tpl_id,
        name,
        data.get("description", ""),
        data.get("category_id"),
        data.get("language", "hindi"),
        data.get("system_prompt", ""),
        data.get("user_prompt_template", ""),
        1 if data.get("is_global", True) else 0
    ))
    conn.commit()
    conn.close()
    return get_prompt_template_by_id(tpl_id)

def update_prompt_template(tpl_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    tpl = get_prompt_template_by_id(tpl_id)
    if not tpl:
        raise ValueError(f"Prompt template '{tpl_id}' not found.")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE prompt_templates SET
        name = ?,
        description = ?,
        category_id = ?,
        language = ?,
        system_prompt = ?,
        user_prompt_template = ?,
        is_global = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        data.get("name", tpl["name"]),
        data.get("description", tpl["description"]),
        data.get("category_id", tpl["category_id"]),
        data.get("language", tpl["language"]),
        data.get("system_prompt", tpl["system_prompt"]),
        data.get("user_prompt_template", tpl["user_prompt_template"]),
        1 if data.get("is_global", tpl["is_global"]) else 0,
        tpl_id
    ))
    conn.commit()
    conn.close()
    return get_prompt_template_by_id(tpl_id)

def delete_prompt_template(tpl_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM prompt_templates WHERE id = ?", (tpl_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": tpl_id}

# Run initialization check on module load
ensure_initialized()
