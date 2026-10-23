import sys
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import requests
import json
import time

url = "http://localhost:11434/api/chat"
story_input = """एक बार नासा के अंतरिक्ष यात्री ने अंतरिक्ष में एक अजीब घंटी जैसी आवाज़ सुनी। सब हैरान थे क्योंकि अंतरिक्ष के निर्वात (वैक्यूम) में तो कोई आवाज़ नहीं हो सकती! बाद में वैज्ञानिकों ने इस रहस्य से पर्दा उठाया।"""

prompt = f"""You are a master viral Hindi YouTube Shorts creator for the COSMOS channel.
The user provided this custom story/script idea:
"{story_input}"

TASK:
1. Understand the core mystery, emotion, and story progression.
2. Expand/adapt it into a captivating 45-50 second viral narration in dramatic, conversational Indian Hindi (Devanagari script, exactly 95-120 words).
3. Start with an irresistible 2-second psychological hook ("क्या आप जानते हैं...").
4. Structure into clear dramatic progression: Hook -> The Shocking Event -> The Investigation -> The Mindblowing Explanation -> Intriguing Question asking viewers to comment.
5. Provide 5 to 6 sequential, highly specific English stock video search keywords matching each scene in exact chronological order (e.g. "astronaut helmet floating space", "spaceship cabin interior dark", "deep space stars silence", "outer space earth solar panels"). Do NOT use vague single words.
6. Provide a punchy 2-4 word Hindi thumbnail hook text.

Respond ONLY with valid JSON (no markdown formatting, no commentary):
{{
  "title": "अंतरिक्ष में सुनाई दी घंटी?! 😱 #shorts",
  "script": "पूर्ण देवनागरी हिंदी नरेशन...",
  "keywords": ["scene1_visual", "scene2_visual", "scene3_visual", "scene4_visual", "scene5_visual"],
  "thumbnail_text": "वैक्यूम में आवाज़?!",
  "description": "अंतरिक्ष का सबसे डरावना रहस्य! #shorts #cosmos #facts #hindi",
  "category": "Space"
}}"""

body = {
    "model": "qwen2.5:7b",
    "messages": [
        {"role": "system", "content": "You are an expert Hindi content director. Always output valid JSON strictly."},
        {"role": "user", "content": prompt}
    ],
    "stream": False,
    "format": "json",
    "options": {"temperature": 0.65}
}

t0 = time.time()
print("Sending request to Ollama qwen2.5:7b...")
resp = requests.post(url, json=body, timeout=120)
print(f"Response in {time.time()-t0:.2f}s, status: {resp.status_code}")
content = resp.json()["message"]["content"]
print("RAW OUTPUT:")
print(content)

try:
    parsed = json.loads(content)
    print("\nPARSED JSON SUCCESS:")
    print("Title:", parsed.get("title"))
    print("Script words:", len(parsed.get("script", "").split()))
    print("Script preview:", parsed.get("script", "")[:120])
    print("Keywords:", parsed.get("keywords"))
    print("Thumbnail Text:", parsed.get("thumbnail_text"))
except Exception as e:
    print(f"JSON Parse Error: {e}")
