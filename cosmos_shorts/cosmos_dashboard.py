import os
import sys
import json
import subprocess
from datetime import datetime
import streamlit as st

# Setup UTF-8 and path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MPT_DIR = os.path.join(BASE_DIR, "MoneyPrinterTurbo")
COSMOS_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(COSMOS_DIR, "output")
TOPICS_PATH = os.path.join(COSMOS_DIR, "cosmos_topics.json")
HISTORY_PATH = os.path.join(COSMOS_DIR, "cosmos_history.json")
CLIENT_SECRET_PATH = os.path.join(COSMOS_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(COSMOS_DIR, "token.json")

if MPT_DIR not in sys.path:
    sys.path.insert(0, MPT_DIR)
if COSMOS_DIR not in sys.path:
    sys.path.insert(0, COSMOS_DIR)

import cosmos_orchestrator
import cosmos_generator
import cosmos_youtube_uploader

st.set_page_config(
    page_title="COSMOS Shorts Creator",
    page_icon="🌌",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #00FF66; margin-bottom: 0px; }
    .sub-title { font-size: 1.05rem; color: #B0BEC5; margin-bottom: 25px; }
    .badge-box { background-color: #121820; border-left: 5px solid #00FF66; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .stTextArea textarea { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 1.05rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌌 COSMOS — YouTube Shorts Automation Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automated Hindi YouTube Shorts creation with Multi-Model AI (Story Conception, Script Mode, or Curated Mysteries)</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Create Short", "📂 Video Library", "🔴 YouTube Upload", "⚙️ AI & System Settings"])

def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else []
    return default if default is not None else []

# TAB 1: CREATE SHORT
with tab1:
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.subheader("1. Creation Mode")
        creation_mode = st.radio(
            "Select how you want to create your video:",
            [
                "🌟 Curated Mystery Topics (100% Pre-tested & Synced)",
                "📖 Write / Paste a Story (AI Understands Plot & Crafts Script)",
                "✍️ Write / Paste an Exact Script (AI Matches Visuals to Your Words)",
                "🏷️ Custom Topic Title (AI Researches & Writes Script)"
            ],
            index=0
        )

        custom_topic = None

        # MODE 1: CURATED TOPICS
        if creation_mode.startswith("🌟 Curated"):
            topics = load_json(TOPICS_PATH, [])
            topic_options = [f"{t.get('category')} — {t.get('topic_hi')}" for t in topics]
            selected_option = st.selectbox("Select Topic", topic_options)
            idx = topic_options.index(selected_option)
            custom_topic = topics[idx]
            custom_topic["mode"] = "curated"

            with st.expander("👀 View Curated Script & Planned Visual Beats", expanded=False):
                st.markdown(f"**Narration Script**:\n\n{custom_topic.get('master_script')}")
                st.markdown(f"**Sequential Visual Beats**: `{', '.join(custom_topic.get('sequential_search_terms', []))}`")

        # MODE 2: WRITE / PASTE A STORY
        elif creation_mode.startswith("📖 Write / Paste a Story"):
            st.info("💡 Write any story concept, summary, or plot points in Hindi, English, or Hinglish. The AI model will understand the narrative, structure an intense 45-second viral Hindi narration, and find matching stock footage.")
            
            c_cat, c_ex = st.columns([2, 1])
            with c_cat:
                story_category = st.selectbox("Story Category", ["Space", "Strange Places", "Science & Nature", "Dangerous Places", "Human History", "Deep Ocean"])
            with c_ex:
                if st.button("🎲 Insert Example Story"):
                    st.session_state["story_input_val"] = "एक बार नासा के अंतरिक्ष यात्री ने अंतरिक्ष में एक अजीब घंटी जैसी आवाज़ सुनी। सब हैरान थे क्योंकि निर्वात (vacuum) में कोई आवाज़ नहीं हो सकती! बाद में वैज्ञानिकों ने इस रहस्य से पर्दा उठाया कि यह आवाज़ स्पेसक्राफ्ट के तापमान बदलने से आ रही थी।"

            user_story = st.text_area(
                "Write your story concept here:",
                value=st.session_state.get("story_input_val", ""),
                placeholder="उदा. 1977 में वैज्ञानिकों को अंतरिक्ष से 72 सेकंड का रहस्यमयी 'Wow!' सिग्नल मिला था...",
                height=130
            )

            custom_topic = {
                "id": f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "mode": "story",
                "category": story_category,
                "custom_story": user_story if user_story else "अंतरिक्ष का एक अनसुलझा रहस्य"
            }

        # MODE 3: WRITE / PASTE AN EXACT SCRIPT
        elif creation_mode.startswith("✍️ Write / Paste an Exact Script"):
            st.info("💡 Paste your own complete Hindi (Devanagari) or English voiceover script. The AI will preserve your words exactly, segment it into sequential visual beats, and download the exact corresponding stock footage.")
            
            script_cat = st.selectbox("Script Category", ["Strange Places", "Space", "Science & Nature", "Dangerous Places", "Human History", "Deep Ocean"])
            
            if st.button("🎲 Insert Example Script"):
                st.session_state["script_input_val"] = "क्या आप जानते हैं हमारे ब्रह्मांड में एक ऐसा ग्रह भी मौजूद है जहां कांच की बारिश होती है? नंबर 1: HD 189733b — यह गहरा नीला ग्रह देखने में पृथ्वी जैसा खूबसूरत लगता है। नंबर 2: लेकिन यहां 8700 किलोमीटर प्रति घंटे की रफ्तार से चलने वाली हवाएं सिलिकेट के नुकीले कणों को उड़ाती हैं। नंबर 3: यहां का तापमान 1000 डिग्री सेल्सियस से भी ज्यादा रहता है। क्या इंसान कभी ऐसे ग्रहों पर कदम रख पाएगा? कमेंट में ज़रूर बताएं!"

            user_script = st.text_area(
                "Paste your exact script here:",
                value=st.session_state.get("script_input_val", ""),
                placeholder="क्या आप जानते हैं हमारी दुनिया में...",
                height=140
            )

            word_count = len(user_script.split()) if user_script else 0
            est_sec = word_count / 2.16 if word_count > 0 else 0
            st.caption(f"📊 Words: **{word_count}** | Estimated Speech Duration: **{est_sec:.1f}s** (Ideal YouTube Short: 40-55s)")

            custom_topic = {
                "id": f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "mode": "script",
                "category": script_cat,
                "custom_script": user_script if user_script else "क्या आप जानते हैं ब्रह्मांड के सबसे बड़े रहस्य के बारे में?"
            }

        # MODE 4: CUSTOM TOPIC TITLE
        else:
            custom_title_hi = st.text_input("Hindi Topic Title", value="बरमूडा ट्रायंगल का असली सच")
            custom_category = st.selectbox("Category", ["Strange Places", "Space", "Science & Nature", "Dangerous Places", "Human History", "Deep Ocean"])
            custom_topic = {
                "id": "topic_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                "mode": "topic",
                "category": custom_category,
                "topic_hi": custom_title_hi,
                "topic_en": custom_title_hi
            }

        st.markdown("---")
        st.subheader("2. Video Styling & Model Selection")
        c_set1, c_set2 = st.columns(2)
        with c_set1:
            caption_pos_choice = st.selectbox(
                "📍 Caption Position",
                [
                    "👇 Bottom (76% Safe Zone - Recommended)",
                    "📍 Lower Third (70%)",
                    "🎯 Center (50%)",
                    "🔝 Top (10%)"
                ]
            )
            pos_map = {
                "👇 Bottom (76% Safe Zone - Recommended)": 76.0,
                "📍 Lower Third (70%)": 70.0,
                "🎯 Center (50%)": 50.0,
                "🔝 Top (10%)": 10.0
            }
            selected_pos = pos_map.get(caption_pos_choice, 76.0)

        with c_set2:
            theme_color_choice = st.selectbox(
                "🎨 Subtitle & Badge Theme Color",
                [
                    "✨ Auto (Match Video Topic Theme)",
                    "🌌 Electric Cyan (#00E5FF - Space / Future)",
                    "🔥 Crimson Fire (#FF2A55 - Danger / Volcano)",
                    "🌿 Neon Emerald (#00FF66 - Nature / Earth)",
                    "🌊 Ocean Aqua (#00D2FF - Deep Sea)",
                    "✨ Ancient Gold (#FFB800 - History / Wonders)",
                    "🔮 Vivid Coral (#FF3366 - Strange Places)",
                    "💜 Neon Violet (#BD00FF - Cosmic / Mystery)"
                ]
            )
            color_map = {
                "✨ Auto (Match Video Topic Theme)": None,
                "🌌 Electric Cyan (#00E5FF - Space / Future)": "#00E5FF",
                "🔥 Crimson Fire (#FF2A55 - Danger / Volcano)": "#FF2A55",
                "🌿 Neon Emerald (#00FF66 - Nature / Earth)": "#00FF66",
                "🌊 Ocean Aqua (#00D2FF - Deep Sea)": "#00D2FF",
                "✨ Ancient Gold (#FFB800 - History / Wonders)": "#FFB800",
                "🔮 Vivid Coral (#FF3366 - Strange Places)": "#FF3366",
                "💜 Neon Violet (#BD00FF - Cosmic / Mystery)": "#BD00FF"
            }
            selected_color = color_map.get(theme_color_choice, None)

        c_v1, c_v2 = st.columns(2)
        with c_v1:
            voice_sel = st.selectbox("Voiceover Narration", ["hi-IN-MadhurNeural-Male (Deep, Cinematic)", "hi-IN-SwaraNeural-Female (Clear, Energetic)"])
        with c_v2:
            avail_models = cosmos_generator.get_available_ollama_models()
            selected_model = st.selectbox("Local AI Model (Ollama)", avail_models, index=0)

        auto_upload_check = st.checkbox("Automatically Upload to YouTube as PRIVATE after rendering", value=False)

        if st.button("🚀 Generate Complete Video & Thumbnail Now", type="primary", use_container_width=True):
            with st.spinner("⏳ Running Pipeline: Script/Story Understanding -> Video (MPT) -> Subtitles (Nirmala) -> Thumbnail..."):
                try:
                    res = cosmos_orchestrator.run_cosmos_short_pipeline(
                        custom_topic=custom_topic,
                        auto_upload=auto_upload_check,
                        subtitle_position="custom",
                        custom_position=selected_pos,
                        theme_color_override=selected_color,
                        preferred_model=selected_model
                    )
                    st.success("🎉 Video & Thumbnail Created Successfully!")
                    st.session_state["latest_job"] = res
                except Exception as e:
                    st.error(f"❌ Error during generation: {e}")

    with col_right:
        st.subheader("Generated Asset Preview")
        latest = st.session_state.get("latest_job")
        if latest:
            content = latest.get("content", {})
            st.markdown(f"**Title**: {content.get('title')}")
            st.markdown(f"**Keywords**: `{', '.join(content.get('keywords', []))}`")

            p_vid, p_thumb = st.columns([1, 1])
            with p_vid:
                video_file = latest["files"]["video"]
                if os.path.exists(video_file):
                    st.video(video_file)
            with p_thumb:
                thumb_file = latest["files"]["thumbnail_png"]
                if os.path.exists(thumb_file):
                    st.image(thumb_file, caption="Vertical 1080x1920 Thumbnail", use_container_width=True)

            with st.expander("📝 View Full Voiceover Script", expanded=False):
                st.write(content.get("script"))
        else:
            st.info("👈 Select your mode (Curated Topic, Custom Story, or Your Own Script) on the left and click **Generate** to create your video!")

# TAB 2: VIDEO LIBRARY
with tab2:
    st.subheader("Completed Videos & Packages")
    history = load_json(HISTORY_PATH, [])
    if not history:
        st.info("No videos in history yet. Generate one in the Create tab!")
    else:
        for item in reversed(history[-10:]):
            job_id = item.get("job_id")
            out_dir = item.get("output_dir", "")
            meta_file = os.path.join(out_dir, "metadata.json")
            meta = load_json(meta_file, {})

            with st.expander(f"🎬 {item.get('title', job_id)} — ({item.get('duration', 0):.1f}s)", expanded=False):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"**Created**: {item.get('created_at')}")
                    st.write(f"**Folder**: `{out_dir}`")
                    st.write(f"**Upload Status**: `{meta.get('upload_status', 'NOT_UPLOADED')}`")
                    if st.button(f"📂 Open Folder in Windows Explorer", key=f"open_{job_id}"):
                        subprocess.run(["explorer", out_dir])
                with c2:
                    vid_path = os.path.join(out_dir, "video.mp4")
                    if os.path.exists(vid_path):
                        st.video(vid_path)
                with c3:
                    thm_path = os.path.join(out_dir, "thumbnail.png")
                    if os.path.exists(thm_path):
                        st.image(thm_path, use_container_width=True)

# TAB 3: YOUTUBE UPLOAD
with tab3:
    st.subheader("🔴 Official YouTube Data API v3 OAuth Integration")
    st.markdown("""
    This uses Google's official, 100% free **YouTube Data API v3** with local OAuth2.
    No subscriptions, no third-party proxies, and no shared passwords.
    """)

    has_client_secret = os.path.exists(CLIENT_SECRET_PATH)
    has_token = os.path.exists(TOKEN_PATH)

    st.write(f"- `client_secret.json`: {'✅ Present' if has_client_secret else '❌ Missing'}")
    st.write(f"- `token.json` (Auth Session): {'✅ Authenticated' if has_token else '⏳ Pending Sign-In'}")

    if has_client_secret and not has_token:
        if st.button("🔑 Connect YouTube Channel (Authorize in Browser)", type="primary"):
            try:
                youtube = cosmos_youtube_uploader.get_youtube_service(CLIENT_SECRET_PATH, TOKEN_PATH)
                st.success("✅ Successfully Authorized your YouTube Channel!")
                st.rerun()
            except Exception as e:
                st.error(f"Authorization error: {e}")

# TAB 4: AI & SYSTEM SETTINGS
with tab4:
    st.subheader("🤖 Local AI Models (Ollama)")
    avail_models = cosmos_generator.get_available_ollama_models()
    st.write(f"**Currently Installed Models**: `{', '.join(avail_models)}`")

    st.markdown("#### ⬇️ Download / Fix / Pull Another Model")
    st.markdown("If you want to try a smaller/faster model or a different architecture, you can pull it directly into Ollama below:")
    
    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        new_model_name = st.selectbox(
            "Select a recommended model to download:",
            [
                "qwen2.5:3b (Super fast ~1.9GB, great for Hindi CPU)",
                "llama3.2:3b (Fast lightweight Meta model)",
                "mistral:7b (High quality European model)",
                "qwen2.5:7b (Already installed — 4.7GB, highest Hindi accuracy)"
            ]
        )
        target_model = new_model_name.split()[0]
    with col_m2:
        st.write("")
        st.write("")
        if st.button(f"Pull `{target_model}`"):
            with st.spinner(f"Downloading `{target_model}` via Ollama... This may take a few minutes depending on internet speed."):
                success = cosmos_generator.pull_ollama_model(target_model)
                if success:
                    st.success(f"✅ Successfully downloaded `{target_model}`!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to download `{target_model}`. Please run `ollama pull {target_model}` in PowerShell.")

    st.markdown("---")
    st.subheader("⚙️ Pipeline Configuration")
    st.write("**Channel**: COSMOS")
    st.write("**Target Duration**: 45-55s")
    st.write("**Default Upload Privacy**: `PRIVATE`")
    st.write("**Timezone**: Asia/Kolkata")
    st.write("**Stock Video Provider**: Pixabay (50+ hits per topic, verified)")
    st.write("**Hindi Devanagari Font**: `Nirmala.ttc` (System native)")
    st.write("**Subtitles**: Word-by-word with spring pop & theme badge")
