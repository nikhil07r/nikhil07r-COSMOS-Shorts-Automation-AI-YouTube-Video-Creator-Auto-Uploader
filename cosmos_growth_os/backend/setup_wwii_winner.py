import sqlite3
import json
from pathlib import Path

db_path = Path(r"C:\Users\nikhil\Downloads\MoneyPrinterTurbo-Portable-Windows-1.3.9\cosmos_growth_os\data\cosmos_growth_os.db")
con = sqlite3.connect(str(db_path))
cur = con.cursor()

# Set all other categories is_default = 0
cur.execute("UPDATE categories SET is_default = 0")

sys_prompt = """You are the Lead Creative Director and Viral Scriptwriter for the YouTube Shorts channel "COSMOS VIRAL".
You are replicating the exact viral retention formula of the channel's #1 most viewed Short: "WWII Soldiers Turned Grenades Into Grappling Hooks" (2,648 views).
Channel Focus: Mind-bending historical warfare hacks, extreme military ingenuity, and impossible battlefield inventions.
Target Duration: Exactly 48-55 seconds (approx 125-145 spoken words).
Mandatory 5-Part Viral Retention Formula:
1. HOOK (0-3s): Start with the impossible tactical hack that stops thumbs scrolling (e.g., "क्या आप जानते हैं कि द्वितीय विश्व युद्ध में सैनिकों ने मौत के ग्रेनेड को रस्सी बांधकर दीवार चढ़ने वाले हुक में बदल दिया था?").
2. CRISIS (4-15s): The extreme life-or-death battlefield situation soldiers faced that forced them to invent this.
3. THE HACK / MECHANISM (15-38s): Step-by-step breakdown of how this crazy invention actually worked mechanically.
4. HISTORICAL CLIMAX (38-48s): The dramatic combat result and lives saved.
5. OUTRO & LOOP (48-55s): Thought-provoking punchline ending with seamless replay loop and "Follow COSMOS for more".
Language: High-energy Hindi with natural Roman-script technical keywords (e.g. WWII, Soldiers, Grenade, Grappling Hook, Tanks).
Stock Keywords: Provide 6 sequential high-definition English stock video keywords matching the scene timeline."""

user_prompt_tpl = """Generate a viral Short in the exact WWII Soldiers Grenade Grappling Hook formula:
Topic / Invention: {prompt}
Category: WWII & Warfare Extreme Inventions
Additional Directives: {extra_instructions}
Language: High-energy Hindi with natural Roman-script technical keywords.
Provide 6 sequential high-definition English stock video keywords matching the scene timeline."""

cur.execute("""
INSERT INTO prompt_templates (id, name, description, category_id, language, system_prompt, user_prompt_template, is_global)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
name=excluded.name,
description=excluded.description,
category_id=excluded.category_id,
language=excluded.language,
system_prompt=excluded.system_prompt,
user_prompt_template=excluded.user_prompt_template,
is_global=excluded.is_global
""", (
    "tpl_wwii_extreme_inventions",
    "WWII & Warfare Extreme Inventions (2.6K Viral Blueprint)",
    "Replicates the 2,648-view WWII Soldiers Turned Grenades Into Grappling Hooks formula.",
    "cat_wwii_extreme_inventions",
    "hindi",
    sys_prompt,
    user_prompt_tpl,
    1
))

instructions = "MODEL DIRECTLY ON THE 2,648-VIEW HIT: Focus on jaw-dropping military adaptations, impossible survival hacks, and secret battlefield inventions. 5-part structure: 0-3s Impossible Hack Hook, 4-15s Life-or-death Crisis, 15-38s Mechanical breakdown, 38-48s Historic combat climax, 48-55s Replay loop outro."

cur.execute("""
INSERT INTO categories (id, name, description, accent_color, text_color, icon, theme_label, visual_style, default_language, default_duration, caption_position_y, caption_font_size, caption_highlight_color, prompt_template_id, custom_prompt_instructions, is_default, is_enabled, order_index)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
name=excluded.name,
description=excluded.description,
accent_color=excluded.accent_color,
text_color=excluded.text_color,
icon=excluded.icon,
theme_label=excluded.theme_label,
visual_style=excluded.visual_style,
default_language=excluded.default_language,
default_duration=excluded.default_duration,
caption_position_y=excluded.caption_position_y,
caption_font_size=excluded.caption_font_size,
caption_highlight_color=excluded.caption_highlight_color,
prompt_template_id=excluded.prompt_template_id,
custom_prompt_instructions=excluded.custom_prompt_instructions,
is_default=excluded.is_default,
is_enabled=excluded.is_enabled,
order_index=excluded.order_index
""", (
    "cat_wwii_extreme_inventions",
    "WWII & Warfare Extreme Inventions (2.6K Formula)",
    "Modeled on your #1 hit (2,648 views). Bizarre tactical hacks, impossible survival inventions, and secret battlefield weapons.",
    "#F59E0B",
    "#000000",
    "🎖️",
    "Tactical Amber (WWII 2.6K)",
    "Cinematic WWII Archival & Military Combat CGI",
    "hindi",
    52,
    76.0,
    70,
    "#F59E0B",
    "tpl_wwii_extreme_inventions",
    instructions,
    1,
    1,
    0
))

con.commit()
con.close()
print("SUCCESS: Registered cat_wwii_extreme_inventions as default category and linked tpl_wwii_extreme_inventions.")
