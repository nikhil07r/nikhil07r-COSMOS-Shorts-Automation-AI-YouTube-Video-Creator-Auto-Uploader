import json
import uuid
import re
import urllib.request
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.config import OLLAMA_BASE_URL, DEFAULT_MODEL, FALLBACK_MODEL, COSMOS_SHORTS_DIR
from backend.database import (
    save_draft, get_drafts, get_categories, get_category_by_id, 
    get_category_by_name, get_prompt_template_by_id
)

router = APIRouter(prefix="/api/studio", tags=["studio"])
logger = logging.getLogger("cosmos.studio")

class GenerationRequest(BaseModel):
    mode: str # "story", "script", "curated"
    prompt: Optional[str] = ""
    exact_script: Optional[str] = ""
    category: Optional[str] = "Space & Universe"
    category_id: Optional[str] = None
    language: Optional[str] = None # "hindi", "hinglish", "english"
    prompt_template_id: Optional[str] = None
    custom_instructions: Optional[str] = ""
    topic: Optional[str] = ""
    model: Optional[str] = DEFAULT_MODEL

class PolicyCheckRequest(BaseModel):
    script: str
    title: str
    language: Optional[str] = "hindi"

def assemble_prompts(req: GenerationRequest):
    """Combines Category settings, Prompt Templates, Language Rules, and User Instructions into predictable prompts."""
    # 1. Resolve Category
    cat_obj = None
    if req.category_id:
        cat_obj = get_category_by_id(req.category_id)
    if not cat_obj and req.category:
        cat_obj = get_category_by_name(req.category)
    
    category_name = cat_obj["name"] if cat_obj else (req.category or "General")
    category_desc = cat_obj["description"] if cat_obj else ""
    cat_instructions = cat_obj.get("custom_prompt_instructions", "") if cat_obj else ""
    visual_style = cat_obj.get("visual_style", "Cinematic Drone") if cat_obj else "Cinematic Drone"
    
    # 2. Resolve Language
    lang = (req.language or (cat_obj.get("default_language") if cat_obj else "hindi") or "hindi").lower()

    # 3. Resolve Prompt Template
    tpl_id = req.prompt_template_id or (cat_obj.get("prompt_template_id") if cat_obj else None)
    tpl_obj = get_prompt_template_by_id(tpl_id) if tpl_id else None

    # Base System Prompt
    if tpl_obj and tpl_obj.get("system_prompt"):
        base_system = tpl_obj["system_prompt"]
    else:
        base_system = f"""You are the Lead Creative Director and Viral Scriptwriter for the YouTube Shorts channel "COSMOS VIRAL".
Channel Identity: High-retention educational Shorts covering {category_name}.
Visual Style: {visual_style}.
Target Duration: Exactly 48-55 seconds (approx 120-145 spoken words).
Structure:
1. Hook (0-4s): Shocking question or cliffhanger statement.
2. Build-up (4-15s): Introduce the mystery with escalating suspense.
3. Rapid Core Facts (15-45s): 3 or 4 mind-bending, verified facts.
4. Outro (45-55s): Thought-provoking punchline and COSMOS subscribe callout ("Follow COSMOS for more")."""

    # Language Directives
    if lang == "hinglish":
        lang_rule = """
CRITICAL LANGUAGE DIRECTIVE:
- Write the narration script in natural, conversational HINGLISH using the ROMAN ALPHABET ONLY (English letters, e.g. "Dosto, kya aapne kabhi socha hai...", "Scientists ne haal hi me ek aisi discovery ki hai...").
- Do NOT output Hindi in Devanagari script. All narration, titles, and on-screen text MUST remain in Roman English letters."""
    elif lang == "english":
        lang_rule = """
CRITICAL LANGUAGE DIRECTIVE:
- Write the entire narration script in clear, compelling, high-impact English."""
    else: # hindi
        lang_rule = """
CRITICAL LANGUAGE DIRECTIVE:
- Write the narration script in natural, high-quality Hindi using the DEVANAGARI SCRIPT.
- Mix standard conversational English technical terms (e.g., 'Black Hole', 'Light Years', 'Scientists') where natural."""

    system_prompt = f"""{base_system}
{lang_rule}

You MUST return ONLY valid JSON matching this schema:
{{
  "title": "Eye-catching Short Title with emoji",
  "category": "{category_name}",
  "hindi_script": "Full spoken narration script according to the language directive...",
  "english_summary": "Brief 2-line English synopsis",
  "keywords": ["5 to 7 English high-definition stock video search terms matching each scene in order"],
  "facts_checklist": ["Fact 1 verified", "Fact 2 verified", "Fact 3 verified"]
}}"""

    # User Prompt
    category_extra = f"\nCategory Specific Directives: {cat_instructions}" if cat_instructions else ""
    user_extra = f"\nPer-Video Custom Instructions: {req.custom_instructions}" if req.custom_instructions else ""

    if req.mode == "story":
        user_prompt = f"""Create a viral Short concept for Category '{category_name}'.
Core Concept / Story Idea: "{req.prompt}"{category_extra}{user_extra}
Ensure the narration flows smoothly, builds escalating curiosity, and provides 5-7 sequential English stock video search queries."""
    elif req.mode == "script":
        user_prompt = f"""The user provided this exact narration script:
"{req.exact_script}"
Analyze this script for category '{category_name}'. Polish wording if needed while strictly keeping the meaning and language format.{category_extra}{user_extra}
Extract:
1. An eye-catching title.
2. English stock footage keywords (5-7 terms matching chronological scene progression).
3. 3-4 key factual checklist points verified from the script.
Return the structured JSON."""
    else: # curated
        user_prompt = f"""Generate a captivating Short script for:
Category: {category_name}
Topic: {req.topic or req.prompt}{category_extra}{user_extra}
Ensure accurate facts, intense suspense hook, and 5-7 sequential English stock video search terms."""

    return system_prompt, user_prompt, {
        "category_name": category_name,
        "accent_color": cat_obj.get("accent_color", "#8B5CF6") if cat_obj else "#8B5CF6",
        "language": lang,
        "visual_style": visual_style
    }

def call_ollama(prompt: str, system_prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    """Invokes local Ollama with native JSON grammar constraint and Core i9 multi-threading."""
    models_to_try = [model_name]
    if model_name != FALLBACK_MODEL:
        models_to_try.append(FALLBACK_MODEL)
    
    last_error = None
    for m in models_to_try:
        try:
            payload = {
                "model": m,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "format": "json",  # Forces native JSON grammar constraint for 100% syntactic accuracy
                "stream": False,
                "options": {
                    "temperature": 0.60,
                    "top_p": 0.90,
                    "num_thread": 16,     # Maximize Core i9-13900H parallel CPU compute
                    "num_ctx": 2048,      # Streamlined context window for 2x faster prompt evaluation
                    "num_predict": 480    # Bound token budget to eliminate trailing latency
                }
            }
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                # Strip think blocks
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                return content.strip()
        except Exception as e:
            logger.warning(f"Failed generation with {m}: {e}")
            last_error = e

    raise HTTPException(status_code=500, detail=f"Ollama generation failed across models: {last_error}")

def extract_json(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    # First: direct parse (succeeds 99.9% of the time with native format: json)
    try:
        return json.loads(raw, strict=False)
    except Exception:
        pass

    # Match markdown code fences ```json ... ``` or raw json
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    candidate = match.group(1) if match else None
    if not candidate:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            candidate = raw[start:end+1]

    if candidate:
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass
        # Clean unescaped internal newlines
        try:
            cleaned = re.sub(r'[\r\n]+', ' ', candidate)
            return json.loads(cleaned, strict=False)
        except Exception:
            pass

    # Regex extraction fallback if JSON syntax was slightly malformed by local model
    fallback = {}
    title_m = re.search(r'"title"\s*:\s*"([^"]+)"', raw)
    if title_m:
        fallback["title"] = title_m.group(1)
    
    script_m = re.search(r'"hindi_script"\s*:\s*"([^"]+)"', raw)
    if script_m:
        fallback["hindi_script"] = script_m.group(1).strip()
    
    kw_m = re.search(r'"keywords"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
    if kw_m:
        keywords = re.findall(r'"([^"]+)"', kw_m.group(1))
        if keywords:
            fallback["keywords"] = keywords

    return fallback

@router.get("/curated_topics")
def get_curated_topics():
    topics_file = COSMOS_SHORTS_DIR / "cosmos_topics.json"
    if topics_file.exists():
        with open(topics_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if isinstance(raw_data, list):
                grouped = {}
                for item in raw_data:
                    cat = item.get("category", "General")
                    if cat not in grouped:
                        grouped[cat] = []
                    grouped[cat].append({
                        "id": item.get("id"),
                        "title": item.get("topic_en") or item.get("topic_hi", "Topic"),
                        "topic_en": item.get("topic_en"),
                        "topic_hi": item.get("topic_hi"),
                        "theme_color": item.get("theme_color"),
                        "script": item.get("master_script"),
                        "keywords": item.get("sequential_search_terms", [])
                    })
                return grouped
            return raw_data
    return {
        "Space & Universe": [{"title": "Black Hole Mystery", "id": "space_01"}],
        "Mysterious Places": [{"title": "Door to Hell Turkmenistan", "id": "places_01"}]
    }

@router.post("/preview_prompt")
def preview_prompt_endpoint(req: GenerationRequest):
    """Returns the assembled system and user prompts without calling the LLM."""
    sys_prompt, user_prompt, meta = assemble_prompts(req)
    return {
        "system_prompt": sys_prompt,
        "user_prompt": user_prompt,
        "metadata": meta
    }

@router.post("/generate")
def generate_concept(req: GenerationRequest):
    sys_prompt, user_prompt, meta = assemble_prompts(req)
    raw_response = call_ollama(user_prompt, sys_prompt, req.model or DEFAULT_MODEL)
    parsed = extract_json(raw_response)
    
    if not parsed or "hindi_script" not in parsed:
        parsed = {
            "title": req.topic or (req.prompt[:40] if req.prompt else "COSMOS Mystery"),
            "category": meta["category_name"],
            "hindi_script": raw_response,
            "english_summary": "Generated educational Short script",
            "keywords": ["cinematic visual", "high tech", "drone shot", "dramatic landscape"],
            "facts_checklist": ["Topic documented", "High engagement pacing"]
        }

    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    draft_obj = {
        "id": draft_id,
        "mode": req.mode,
        "title": parsed.get("title", "COSMOS Short"),
        "category": parsed.get("category", meta["category_name"]),
        "hindi_script": parsed.get("hindi_script", ""),
        "english_script": parsed.get("english_summary", ""),
        "keywords": parsed.get("keywords", []),
        "facts_checklist": parsed.get("facts_checklist", []),
        "status": "ready"
    }
    save_draft(draft_obj)
    
    return draft_obj

@router.post("/policy_check")
def policy_and_quality_check(req: PolicyCheckRequest):
    words = req.script.split()
    word_count = len(words)
    lang = (req.language or "hindi").lower()
    
    # Ideal Shorts duration check (at 2.5 words per second spoken rate)
    est_duration_sec = round(word_count / 2.5, 1)
    duration_status = "perfect" if (45 <= est_duration_sec <= 60) else ("too_short" if est_duration_sec < 45 else "too_long")
    
    # Sensationalism & Guidelines
    sensational_words = ["सब मर जाएंगे", "तबाही", "प्रलय आ गई", "100% fake", "खून", "guaranteed profit", "100% returns", "get rich quick"]
    flagged_terms = [w for w in sensational_words if w.lower() in req.script.lower()]
    
    if lang == "hinglish":
        has_hook = any(mark in req.script[:70].lower() for mark in ["?", "kya", "kabhi", "socha", "why", "how", "imagine", "did you know", "secret", "shocking"])
        has_callout = any(call in req.script[-100:].lower() for call in ["cosmos", "subscribe", "follow", "share", "like"])
    else:
        has_hook = any(mark in req.script[:60] for mark in ["?", "क्या", "कभी सोचा", "कल्पना", "रहस्य"])
        has_callout = any(call in req.script[-100:] for call in ["COSMOS", "सब्सक्राइब", "फॉलो", "लाइक"])
    
    score = 100
    suggestions = []
    
    if duration_status == "too_short":
        score -= 15
        suggestions.append(f"Script is slightly short ({est_duration_sec}s). Add 1 more fascinating fact to reach 50s.")
    elif duration_status == "too_long":
        score -= 20
        suggestions.append(f"Script might exceed 60s Shorts limit ({est_duration_sec}s). Trim roughly {word_count - 145} words.")
    
    if not has_hook:
        score -= 15
        suggestions.append("Hook recommendation: Start with a gripping question in the first 3 seconds.")
        
    if not has_callout:
        score -= 10
        suggestions.append("Callout recommendation: Mention 'Follow COSMOS' in the final 5 seconds.")

    if flagged_terms:
        score -= 15
        suggestions.append(f"Notice: Sensationalist phrases detected ({', '.join(flagged_terms)}). Keep claims grounded and verified.")

    return {
        "word_count": word_count,
        "est_duration_seconds": est_duration_sec,
        "duration_status": duration_status,
        "quality_score": max(20, score),
        "guidelines_compliant": len(flagged_terms) == 0,
        "has_strong_hook": has_hook,
        "has_branding_outro": has_callout,
        "suggestions": suggestions
    }

@router.get("/drafts")
def list_drafts(limit: int = 20):
    return {"drafts": get_drafts(limit=limit)}

@router.post("/drafts/save")
def save_custom_draft(draft: Dict[str, Any]):
    if "id" not in draft:
        draft["id"] = f"draft_{uuid.uuid4().hex[:8]}"
    save_draft(draft)
    return {"status": "saved", "draft": draft}

@router.post("/suggest_topic")
def suggest_viral_topic(payload: Dict[str, Any] = None):
    category = (payload or {}).get("category", "WWII & Warfare Extreme Inventions (2.6K Formula)")
    
    prompt = f"""You are the Lead Creative Director for COSMOS VIRAL, specialized in replicating the channel's top hit "WWII Soldiers Turned Grenades Into Grappling Hooks" (2,648 views).
Suggest 1 fresh, jaw-dropping, verified historical military invention or extreme combat survival hack that sounds completely impossible.
Category: {category}
Focus on: Bizarre WWII inventions, ingenious soldier improvisations, or unbelievable battlefield adaptations.

Return ONLY clean JSON:
{{
  "topic": "Concise topic title in English (under 60 chars)",
  "hook_preview": "Gripping first 3-second spoken sentence in Hindi...",
  "category": "{category}"
}}"""

    system_prompt = "You are an elite viral YouTube Shorts researcher. Return ONLY valid JSON."
    try:
        raw = call_ollama(prompt, system_prompt)
        parsed = extract_json(raw)
        if parsed and "topic" in parsed:
            return parsed
    except Exception as e:
        logger.warning(f"Error suggesting topic: {e}")

    fallbacks = [
        {"topic": "Project Pigeon: The Secret WWII Missiles Guided by Trained Birds", "hook_preview": "क्या आप जानते हैं कि द्वितीय विश्व युद्ध में वैज्ञानिकों ने मिसाइल को गाइड करने के लिए जिंदा कबूतरों को ट्रेन किया था?"},
        {"topic": "The Inflatable Ghost Army That Fooled Hitler with Rubber Tanks", "hook_preview": "क्या आप यकीन करेंगे कि 1,100 कलाकारों ने सिर्फ रबर के गुब्बारे वाले टैंकों से हिटलर की सेना को चकमा दे दिया था?"},
        {"topic": "How a 19-Year-Old WWII Gunner Fell 20,000 Feet Without Parachute and Survived", "hook_preview": "20,000 फीट की ऊंचाई से बिना पैराशूट के गिरना और जिंदा बच जाना — सुनिए इस जांबाज सैनिक की खौफनाक कहानी!"},
        {"topic": "Why WWII Submariners Poured Coffee Grounds into Leaking Torpedo Tubes", "hook_preview": "समुद्र के 300 फीट नीचे जब पनडुब्बी में पानी भरने लगा, तो कॉफी पाउडर ने 80 सैनिकों की जान कैसे बचाई?"}
    ]
    import random
    fb = random.choice(fallbacks)
    return {
        "topic": fb["topic"],
        "hook_preview": fb["hook_preview"],
        "category": category
    }
