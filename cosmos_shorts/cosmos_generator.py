import os
import sys
import json
import re
import requests
import subprocess
from typing import Dict, Any, Optional, List

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
DEFAULT_MODEL = "qwen2.5:7b"
FALLBACK_MODELS = ["qwen2.5:7b", "qwen2.5:3b", "llama3.2", "mistral"]

_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)
_UNCLOSED_THINK_RE = re.compile(r"<think\b[^>]*>.*$", re.IGNORECASE | re.DOTALL)

def clean_llm_response(text: str) -> str:
    text = _THINK_BLOCK_RE.sub("", text)
    text = _UNCLOSED_THINK_RE.sub("", text)
    return text.strip()

def get_available_ollama_models() -> List[str]:
    """Returns list of currently installed Ollama model names."""
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            names = [m.get("name") for m in models_data if m.get("name")]
            return names if names else [DEFAULT_MODEL]
    except Exception:
        pass
    return [DEFAULT_MODEL]

def pull_ollama_model(model_name: str) -> bool:
    """Pulls/downloads a model in Ollama if missing."""
    try:
        print(f"[Ollama] Downloading/verifying model: {model_name}...")
        res = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True, check=True)
        return True
    except Exception as e:
        print(f"[Ollama] Failed to pull {model_name}: {e}")
        return False

def call_ollama_json(prompt: str, preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries Ollama expecting JSON output, with automatic model fallback.
    """
    available = get_available_ollama_models()
    candidates = []
    if preferred_model:
        candidates.append(preferred_model)
    for m in FALLBACK_MODELS:
        if m not in candidates:
            candidates.append(m)

    last_error = None
    for model in candidates:
        # Check if model exists or can be used
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a master viral Hindi YouTube Shorts creator. You strictly output valid JSON only, without markdown fences or extra commentary."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.65}
        }

        try:
            print(f"[LLM] Generating with model: {model}...")
            resp = requests.post(OLLAMA_API_URL, json=body, timeout=120)
            if resp.status_code == 200:
                raw = resp.json()["message"]["content"]
                cleaned = clean_llm_response(raw)
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                data = json.loads(cleaned)
                print(f"[LLM] Generation successful with model: {model}")
                return data
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            last_error = e
            print(f"[LLM] Model {model} attempt failed: {e}. Trying fallback...")

    raise RuntimeError(f"All Ollama models failed. Last error: {last_error}")

def sanitize_content_dict(data: Dict[str, Any], default_category: str = "General") -> Dict[str, Any]:
    # Clean script text
    script_text = data.get("script", "")
    script_text = re.sub(r"[\*#_\[\]\(\)]", " ", script_text)
    script_text = re.sub(r"\b(shorts|cosmos|facts|hindi|viral|trending)\b", "", script_text, flags=re.IGNORECASE)
    script_text = re.sub(r"\s+", " ", script_text).strip()
    data["script"] = script_text

    # Clean sequential keywords
    cleaned_keywords = []
    for kw in data.get("keywords", []):
        k = str(kw).replace("_", " ").strip()
        if k and k.lower() not in [x.lower() for x in cleaned_keywords]:
            cleaned_keywords.append(k)
    data["keywords"] = cleaned_keywords if cleaned_keywords else ["planet earth space", "galaxy stars night"]

    # Thumbnail text
    thumb = data.get("thumbnail_text", "ये सच में है?!")
    thumb = re.sub(r'[\U00010000-\U0010ffff]|#\w+', '', thumb).strip()
    data["thumbnail_text"] = thumb if thumb else "कांप उठेंगे आप!"

    # Title
    title = data.get("title", "रहस्यमयी घटना 😱 #shorts")
    if "#shorts" not in title.lower():
        title = f"{title.strip()} #shorts"
    data["title"] = title

    # Description & Tags
    data["tags"] = data.get("tags", ["COSMOS", "Shorts", "Hindi Facts", default_category])
    data["description"] = data.get("description", f"{title}\n\nSubscribe to COSMOS! #shorts #cosmos #facts #hindi")
    return data

def generate_from_story(story_text: str, category: str = "General", preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Mode: Story Conception.
    Understands the user's custom story/concept (Hindi, English, Hinglish, rough notes).
    Converts it into a dramatic 45-50 second viral Hindi voiceover narration (Devanagari, ~100-115 words)
    with 5 to 7 chronologically sequential visual search queries matching each beat.
    """
    prompt = f"""You are a master viral Hindi YouTube Shorts content director (for channel "COSMOS").
The user provided this custom story / plot idea:
\"\"\"{story_text.strip()}\"\"\"

Category: {category}

STRICT CREATIVE INSTRUCTIONS:
1. DEEP STORY COMPREHENSION: Understand the core mystery, plot arc, climax, and scientific/dramatic wonder of the story.
2. VIRAL SCRIPT (Devanagari Hindi):
   - Length: Exactly 95 to 115 Hindi words (matches a 45-50 second voiceover at standard pace).
   - Hook (First 2 seconds): Irresistible psychological hook (e.g. "क्या आप जानते हैं...", "ज़रा सोचिए अगर...").
   - Structure: Chronological story progression with intense dramatic pacing: The Hook ➔ The Incident ➔ The Escalation ➔ The Revelation ➔ Intriguing ending question inviting viewers to comment.
   - Tone: Conversational, dramatic Indian Hindi (like Dhruv Rathee or FactoBoi). NEVER use awkward literal translations.
3. SEQUENTIAL VISUAL SEARCH KEYWORDS:
   - Provide EXACTLY 5 to 7 sequential, highly specific English stock video search keywords matching each section of the narration in exact chronological order.
   - Examples: "astronaut floating dark space", "creepy alien landscape rocks", "blue bioluminescent cave", "deep ocean monster shadows".
   - DO NOT use vague words like 'nature', 'landscape', 'dark', 'desert'.
4. THUMBNAIL BADGE TEXT:
   - 2 to 4 ultra-punchy Hindi words for the video thumbnail badge (e.g. "वैक्यूम में आवाज़?!", "रहस्यमयी दरवाज़ा!").

Return ONLY valid JSON in this exact structure:
{{
  "title": "Dramatic Catchy Hindi Title with 1 emoji and #shorts",
  "script": "Complete narration in Devanagari script without markdown or asterisks",
  "keywords": ["scene1_visual", "scene2_visual", "scene3_visual", "scene4_visual", "scene5_visual"],
  "thumbnail_text": "2 to 4 powerful Hindi words",
  "description": "Engaging 2-line Hindi description with #shorts #cosmos #facts #hindi",
  "tags": ["COSMOS", "Shorts", "Hindi Facts", "{category}"]
}}"""

    data = call_ollama_json(prompt, preferred_model)
    return sanitize_content_dict(data, category)

def extract_keywords_from_script(script_text: str, editing_style: str = "", category: str = "General", preferred_model: Optional[str] = None) -> List[str]:
    """
    Extracts sequential stock video search keywords matching the user's exact manual script
    and their video editing style instructions (e.g. fast cuts, dark cinematic tone).
    """
    clean_script = script_text.strip()
    prompt = f"""You are an expert visual director and editor for YouTube Shorts.
The user provided their own exact narration script:
"""{clean_script}"""

Category: {category}
Video Editing Style & Animation Directives: {editing_style or "High retention, dynamic visual pacing"}

TASK:
Break down the script chronologically into 5 to 7 sequential visual beats.
For each beat, provide an exact English stock footage search term matching the narration and editing style.
Make sure the terms reflect the requested editing style and aesthetic.

Return ONLY valid JSON:
{{
  "keywords": ["scene1_visual_term", "scene2_visual_term", "scene3_visual_term", "scene4_visual_term", "scene5_visual_term"]
}}"""
    try:
        res = call_ollama_json(prompt, preferred_model)
        kws = res.get("keywords", [])
        if isinstance(kws, list) and len(kws) >= 3:
            return kws[:7]
    except Exception as e:
        print(f"[Keywords] Extraction fallback: {e}")

    # Fallback to smart terms
    return [f"{category} cinematic footage", "dramatic atmospheric landscape", "high resolution close up"]

def generate_from_script(script_text: str, category: str = "General", editing_style: str = "", preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Mode: Direct Custom Script.
    Preserves the user's exact manual narration script 100% verbatim in the given language.
    Analyzes the script and editing style prompt to extract matching visual search keywords,
    catchy title, and metadata.
    """
    clean_script = script_text.strip()
    prompt = f"""You are an expert visual director for the COSMOS YouTube Shorts channel.
The user has provided their own exact narration script:
"""{clean_script}"""

Category: {category}
Video Editing Style & Animation Directives: {editing_style or "Dynamic, high retention, cinematic"}

TASK:
1. SEQUENTIAL VISUAL KEYWORDS:
   - Break this narration down into 5 to 7 chronological visual beats.
   - Provide EXACTLY 5 to 7 sequential, highly specific English stock video search queries matching each beat.
   - Incorporate the requested video editing style and visual tone.
2. TITLE & METADATA:
   - Catchy title matching the script with 1 emoji and #shorts.
3. THUMBNAIL HOOK:
   - Punchy 2 to 4 word hook phrase.

Return ONLY valid JSON:
{{
  "title": "Short Title with emoji #shorts",
  "keywords": ["beat1_visual", "beat2_visual", "beat3_visual", "beat4_visual", "beat5_visual"],
  "thumbnail_text": "2-4 words hook",
  "description": "Engaging description #shorts #cosmos #viral",
  "tags": ["COSMOS", "Shorts", "{category}"]
}}"""

    data = call_ollama_json(prompt, preferred_model)
    # Strictly preserve the user's exact manual script in whatever language they provided
    data["script"] = clean_script

    return sanitize_content_dict(data, category)

def generate_from_topic(topic_hi: str, topic_en: str, category: str = "General", preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Mode: Custom Topic Title.
    Generates a full 45-50s script from a given topic title.
    """
    prompt = f"""You are a professional Hindi viral YouTube Shorts scriptwriter for channel "COSMOS".
Write an engaging 45-50 second script in natural, conversational, dramatic Indian Hindi (Devanagari script).

Topic: {topic_hi} ({topic_en})
Category: {category}

RULES:
1. Start with an irresistible 2-second psychological hook in natural Hindi.
2. Cover 3 to 4 striking, factually true points using clear markers: "नंबर 1: ...", "नंबर 2: ...", "नंबर 3: ...".
3. Exactly 95-115 Hindi words (45-50 seconds audio).
4. End with an intriguing question inviting comments.
5. Provide 5 to 7 sequential, highly specific English stock video search keywords matching each section in chronological order. Avoid generic words.
6. Provide a punchy 2-4 word Hindi thumbnail hook text.

Return ONLY valid JSON:
{{
  "title": "{topic_hi} 😱 #shorts",
  "script": "Complete narration in Devanagari script",
  "keywords": ["scene1_visual", "scene2_visual", "scene3_visual", "scene4_visual", "scene5_visual"],
  "thumbnail_text": "2-4 words Hindi",
  "description": "{topic_hi}! #shorts #cosmos #facts #hindi",
  "tags": ["COSMOS", "Shorts", "Hindi Facts", "{category}"]
}}"""

    data = call_ollama_json(prompt, preferred_model)
    return sanitize_content_dict(data, category)

def generate_cosmos_content(topic_info: Dict[str, Any], preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Universal dispatcher:
    1. Direct Script Mode: if topic_info has 'custom_script' or mode == 'script'
    2. Story Mode: if topic_info has 'custom_story' or mode == 'story'
    3. Curated Master Topic: if topic_info has 'master_script' and 'sequential_search_terms'
    4. Custom Topic Title: default fallback
    """
    mode = topic_info.get("mode")
    category = topic_info.get("category", "General")

    # Mode 1: Exact Manual Script (Highest priority - preserves user's exact script & editing style)
    if mode == "script" or topic_info.get("custom_script") or topic_info.get("script"):
        script = topic_info.get("custom_script") or topic_info.get("script", "")
        editing_style = topic_info.get("editing_style") or topic_info.get("custom_instructions", "")
        return generate_from_script(script, category=category, editing_style=editing_style, preferred_model=preferred_model)

    # Mode 2: Story Conception
    if mode == "story" or topic_info.get("custom_story"):
        story = topic_info.get("custom_story") or topic_info.get("story", "")
        return generate_from_story(story, category=category, preferred_model=preferred_model)

    # Mode 3: Curated Master Topic
    if topic_info.get("master_script") and topic_info.get("sequential_search_terms"):
        topic_hi = topic_info.get("topic_hi", "दुनिया के सबसे बड़े रहस्य")
        return {
            "title": f"{topic_hi} 😱 #shorts",
            "script": topic_info["master_script"],
            "keywords": topic_info["sequential_search_terms"],
            "description": f"{topic_hi}! प्रकृति और ब्रह्मांड के सबसे अद्भुत रहस्य। Subscribe to COSMOS! #shorts #cosmos #facts #hindi",
            "thumbnail_text": topic_info.get("thumbnail_text", "ये सच में है?!"),
            "tags": ["COSMOS", "Shorts", "Hindi Facts", category, "Amazing Facts"]
        }

    # Mode 4: Topic Title
    topic_hi = topic_info.get("topic_hi", "ब्रह्मांड के रहस्य")
    topic_en = topic_info.get("topic_en", topic_hi)
    return generate_from_topic(topic_hi, topic_en, category=category, preferred_model=preferred_model)
