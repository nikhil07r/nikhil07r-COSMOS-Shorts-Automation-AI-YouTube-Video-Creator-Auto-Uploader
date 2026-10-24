import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database import get_videos, get_channel
from backend.routers.studio import call_ollama, extract_json

router = APIRouter(prefix="/api/growth", tags=["growth"])
logger = logging.getLogger("cosmos.growth")

class ReviveHookRequest(BaseModel):
    video_id: Optional[str] = None
    title: str
    script: Optional[str] = ""
    language: Optional[str] = "hindi"

class InstagramBundleRequest(BaseModel):
    title: str
    category: Optional[str] = "Space & Universe"
    language: Optional[str] = "hindi"

@router.get("/diagnostics")
def get_algorithm_diagnostics():
    """
    Analyzes channel videos and diagnoses why videos are stuck at 0-3 views,
    identifying algorithmic bottlenecks (Swipe-away rate, invalid traffic, SEO).
    """
    ch = get_channel()
    videos = get_videos(limit=50)

    total_videos = len(videos)
    zero_view_vids = []
    low_view_vids = []
    breakout_vids = []

    for v in videos:
        views = v.get("view_count", 0)
        v_info = {
            "video_id": v["video_id"],
            "title": v.get("title", "Untitled"),
            "view_count": views,
            "like_count": v.get("like_count", 0),
            "comment_count": v.get("comment_count", 0),
            "published_at": v.get("published_at"),
            "thumbnail_url": v.get("thumbnail_url")
        }
        if views <= 5:
            zero_view_vids.append(v_info)
        elif views < 300:
            low_view_vids.append(v_info)
        else:
            breakout_vids.append(v_info)

    # Health & Diagnosis calculations
    stuck_pct = round((len(zero_view_vids) / max(1, total_videos)) * 100, 1)

    diagnostic_factors = [
        {
            "factor": "Self-Viewing Penalty (CRITICAL)",
            "severity": "high",
            "detected": len(zero_view_vids) > 0,
            "title": "Watching your own Shorts from another account freezes views!",
            "explanation": "YouTube detects identical IP addresses and Wi-Fi networks. When you watch your own videos repeatedly, YouTube's anti-spam algorithm flags it as 'Invalid Traffic' and freezes distribution to 0-3 views for days.",
            "action": "STOP watching your videos from your own phone/Wi-Fi. Let the algorithm push it organically to real viewers."
        },
        {
            "factor": "0-3s Swipe-Away Barrier",
            "severity": "high",
            "detected": True,
            "title": "Swipe-Away Rate above 30% kills distribution",
            "explanation": "YouTube tests new Shorts with a small seed audience (20-100 people). If over 30% swipe away within the first 2 seconds, YouTube immediately cuts all impressions to zero.",
            "action": "Use intense cliffhanger curiosity hooks (e.g. 'अगर ऐसा हुआ तो क्या होगा?', 'नासा ने इसे क्यों छुपाया?') in the first 2 seconds."
        },
        {
            "factor": "Shorts SEO & Tag Visibility",
            "severity": "medium",
            "detected": True,
            "title": "Missing Search & Feed Category Triggers",
            "explanation": "Shorts without clear keyword tags (#Shorts, #SpaceFacts, #HindiFacts) get lost because the algorithm does not know which viewer group to test them with.",
            "action": "Always keep titles between 35-55 characters with 1 curiosity hook, 1 emoji, and #Shorts."
        },
        {
            "factor": "Cross-Platform Velocity",
            "severity": "medium",
            "detected": True,
            "title": "Zero External Traffic Signals",
            "explanation": "Channels that cross-post to Instagram Reels and bring external traffic to YouTube get 3x faster seed batch testing because YouTube rewards external audience acquisition.",
            "action": "Repost every Short to Instagram Reels with our 1-click Instagram Bundle."
        }
    ]

    return {
        "channel_title": ch.get("title", "COSMOS VIRAL") if ch else "COSMOS VIRAL",
        "total_videos": total_videos,
        "stuck_videos_count": len(zero_view_vids),
        "stuck_percentage": stuck_pct,
        "zero_view_videos": zero_view_vids[:10],
        "breakout_videos": breakout_vids[:5],
        "diagnostic_factors": diagnostic_factors,
        "algorithm_verdict": "Algorithm Cold Start & Invalid Traffic Freeze detected. Follow the recovery plan to trigger seed batch testing."
    }

@router.post("/revive_hook")
def generate_revival_hooks(req: ReviveHookRequest):
    """
    Uses local Ollama to craft 3 ultra-viral curiosity hooks and optimized titles
    to revive a stuck video and maximize the Viewed vs Swiped-Away ratio (>75%).
    """
    prompt = f"""You are a YouTube Shorts Algorithm Specialist and Viral Retention Expert for Hindi educational content.
Analyze this underperforming video title / topic:
Title: "{req.title}"
{f'Script snippet: "{req.script[:200]}"' if req.script else ''}
Language: {req.language}

The video is stuck at 0-3 views because viewers are swiping away in the first 2 seconds.
Create 3 distinct, high-CTR viral hook alternatives that stop viewers from swiping away:
1. The Curiosity Gap Hook (Creates an intense open loop)
2. The Shocking Secret Hook (Reveals something hidden or forbidden)
3. The What-If / Fear of Unknown Hook (High engagement emotional trigger)

Also provide:
- A high-CTR viral Title (under 50 chars with emoji and #Shorts)
- Top 5 algorithmic tags

Return ONLY clean JSON:
{{
  "curiosity_hook": "First 3-second spoken sentence...",
  "shock_hook": "First 3-second spoken sentence...",
  "what_if_hook": "First 3-second spoken sentence...",
  "optimized_title": "Short title with emoji #Shorts",
  "predicted_retention_boost": "+45% Viewed vs Swiped",
  "tags": ["#Shorts", "#COSMOS", "#HindiFacts", "#SpaceMystery", "#ViralShorts"]
}}"""

    system_prompt = "You are an elite YouTube Shorts Growth Strategist. Return ONLY valid JSON."
    
    try:
        raw = call_ollama(prompt, system_prompt)
        parsed = extract_json(raw)
        if parsed and "curiosity_hook" in parsed:
            return parsed
    except Exception as e:
        logger.warning(f"Revive hook Ollama error: {e}")

    # Fallback high-impact hooks
    return {
        "curiosity_hook": "क्या आपने कभी सोचा है कि अगर अंतरिक्ष का ये रहस्य सच हो गया, तो धरती का क्या होगा?",
        "shock_hook": "नासा ने 40 साल तक इस एक रहस्य को दुनिया से छुपाकर रखा था!",
        "what_if_hook": "कल्पना कीजिए कि कल सुबह आसमान से सूरज हमेशा के लिए गायब हो जाए!",
        "optimized_title": f"नासा का सबसे डरावना सच! 😱 #Shorts",
        "predicted_retention_boost": "+50% Viewed vs Swiped",
        "tags": ["#Shorts", "#COSMOS", "#SpaceMysteries", "#HindiFacts", "#Viral"]
    }

@router.post("/instagram_bundle")
def generate_instagram_bundle(req: InstagramBundleRequest):
    """
    Generates a complete Instagram Reels package (viral caption, call-to-action,
    and 30 categorized hashtags) so the user can cross-post and drive external views.
    """
    prompt = f"""Generate a high-converting Instagram Reels post bundle for:
Title: "{req.title}"
Category: "{req.category}"
Language: "{req.language}"

Include:
1. Catchy 2-line caption with curiosity hook in Hindi/Hinglish.
2. Direct Call To Action (CTA) telling viewers to check out YouTube channel "COSMOS VIRAL" for full mysteries.
3. 25-30 targeted hashtags grouped into Niche, Trending, and Reach tags.
4. Recommended audio style.

Return ONLY clean JSON:
{{
  "caption": "Catchy Instagram caption with emojis...",
  "cta": "Follow @cosmos.viral & Subscribe on YouTube (link in bio) for daily space mysteries! 🪐",
  "hashtags": "#spacefacts #mysteriousfacts #hindifacts #universe #reelsindia #trendingreels #shorts #sciencefacts #isro #nasa #viralreels #dailyfacts #didyouknow #earthmysteries #knowledgeispower",
  "audio_recommendation": "Use trending suspense / dark synth cinematic audio",
  "best_time_to_post": "18:00 – 21:00 IST (Evening Peak)"
}}"""

    system_prompt = "You are a Social Media Viral Growth Manager specializing in Instagram Reels. Return ONLY valid JSON."
    
    try:
        raw = call_ollama(prompt, system_prompt)
        parsed = extract_json(raw)
        if parsed and "caption" in parsed:
            return parsed
    except Exception as e:
        logger.warning(f"Instagram bundle Ollama error: {e}")

    return {
        "caption": f"ब्रह्मांड का एक ऐसा रहस्य जो आपके होश उड़ा देगा! 🌌 क्या आपको इसके बारे में पता था? कमेंट में बताएं!\n\nपूरे वीडियो और रहस्यों के लिए हमारे YouTube चैनल 'COSMOS VIRAL' को सब्सक्राइब करें! 🔴",
        "cta": "Follow @cosmos.viral & YouTube link in bio! 🪐",
        "hashtags": "#spacefacts #hindifacts #mysteriousfacts #reelsindia #trendingreels #sciencefacts #universe #nasa #isro #didyouknow #factsinhindi #dailyfacts #viralreels #reelsviral #explorepage #cosmos",
        "audio_recommendation": "Trending dark mystery / cinematic suspense audio",
        "best_time_to_post": "18:30 IST (Prime Engagement Hour)"
    }

@router.get("/milestone_roadmap")
def get_milestone_roadmap():
    """
    Provides an exact math-backed blueprint to reach YouTube Partner Program monetization
    from 49 subscribers to 1,000 subscribers and 10 Million Shorts views.
    """
    ch = get_channel() or {"subscriber_count": 49, "view_count": 11340}
    current_subs = ch.get("subscriber_count", 49)
    current_views = ch.get("view_count", 11340)

    target_subs = 1000
    target_views = 10_000_000

    remaining_subs = max(0, target_subs - current_subs)
    remaining_views = max(0, target_views - current_views)

    # 90-day trajectory roadmap
    daily_views_needed_90d = round(remaining_views / 90)
    daily_subs_needed_90d = round(remaining_subs / 90, 1)

    phases = [
        {
            "phase": 1,
            "name": "Break the Zero-View Trap (Seed Batch Activation)",
            "goal": "Get first 500 – 2,000 views per Short",
            "metric": "Viewed vs Swiped > 70%",
            "status": "In Progress" if current_views < 25000 else "Completed",
            "steps": [
                "Stop watching your own Shorts from personal devices/Wi-Fi to clear Invalid Traffic flag.",
                "Craft cliffhanger hooks in the first 0-3 seconds using AI Hook Laboratory.",
                "Post 1 Short daily at exactly 18:30 IST (when audience retention peaks)."
            ]
        },
        {
            "phase": 2,
            "name": "Build Audience Momentum & First 500 Subscribers",
            "goal": "Reach 500 Subscribers & 100K Views",
            "metric": "Average Percentage Viewed (APV) > 85%",
            "status": "Next" if current_subs < 500 else "Completed",
            "steps": [
                "Repurpose every Short to Instagram Reels with link in bio.",
                "Pin an engaging question in the YouTube comments to boost engagement score.",
                "Maintain 1-to-1 visual pacing (scene changes every 4-5 seconds)."
            ]
        },
        {
            "phase": 3,
            "name": "Viral Algorithmic Outlier",
            "goal": "1 to 3 viral breakout Shorts hitting 500K - 1M+ views",
            "metric": "Engagement Rate > 8%",
            "status": "Upcoming",
            "steps": [
                "Double down on highest performing categories (Space & Earth Mysteries).",
                "Use high-contrast 1080x1920 thumbnail badges to drive CTR from channel page.",
                "Consistent daily posting triggers YouTube recommendation algorithm."
            ]
        },
        {
            "phase": 4,
            "name": "YouTube Partner Program (YPP) Monetization",
            "goal": "1,000 Subscribers + 10M Shorts Views -> Start Earning Ad Revenue!",
            "metric": "Eligible for AdSense & YouTube Shorts Revenue Sharing",
            "status": "Goal",
            "steps": [
                "Apply for monetization in YouTube Studio.",
                "Earn passive monthly revenue from YouTube Shorts Ad Pool.",
                "Add sponsorship mentions and brand deals in video descriptions."
            ]
        }
    ]

    return {
        "current_subs": current_subs,
        "current_views": current_views,
        "remaining_subs": remaining_subs,
        "remaining_views": remaining_views,
        "daily_views_needed": daily_views_needed_90d,
        "daily_subs_needed": daily_subs_needed_90d,
        "phases": phases
    }
