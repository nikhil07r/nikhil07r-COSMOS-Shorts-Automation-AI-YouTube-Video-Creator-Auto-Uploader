import os
import sys
import argparse
import json

# Setup UTF-8 and path
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(__file__))
import cosmos_orchestrator
import cosmos_generator

def parse_args():
    parser = argparse.ArgumentParser(description="COSMOS Shorts Creator CLI")
    parser.add_argument("--mode", choices=["topic", "story", "script"], default="topic", help="Creation mode")
    parser.add_argument("--story", type=str, default="", help="Custom story concept or summary")
    parser.add_argument("--story-file", type=str, default="", help="Path to text file containing story")
    parser.add_argument("--script", type=str, default="", help="Exact voiceover script")
    parser.add_argument("--script-file", type=str, default="", help="Path to text file containing script")
    parser.add_argument("--topic-id", type=str, default="", help="Curated topic ID (e.g. space_01, strange_places_01)")
    parser.add_argument("--category", type=str, default="Space", help="Category for the short")
    parser.add_argument("--model", type=str, default="", help="Ollama model to use (e.g. qwen2.5:7b, qwen2.5:3b)")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube as PRIVATE after rendering")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 1. Determine Input Mode
    custom_topic = {}
    
    if args.story or args.story_file or args.mode == "story":
        story_text = args.story
        if args.story_file and os.path.exists(args.story_file):
            with open(args.story_file, "r", encoding="utf-8") as f:
                story_text = f.read()
        if not story_text:
            story_text = "अंतरिक्ष का एक डरावना रहस्य"
            
        custom_topic = {
            "mode": "story",
            "category": args.category,
            "custom_story": story_text
        }
        print(f"📖 Running in STORY CONCEPTION Mode...")
        
    elif args.script or args.script_file or args.mode == "script":
        script_text = args.script
        if args.script_file and os.path.exists(args.script_file):
            with open(args.script_file, "r", encoding="utf-8") as f:
                script_text = f.read()
        if not script_text:
            script_text = "क्या आप जानते हैं हमारे ब्रह्मांड के सबसे बड़े रहस्य के बारे में?"
            
        custom_topic = {
            "mode": "script",
            "category": args.category,
            "custom_script": script_text
        }
        print(f"✍️ Running in EXACT SCRIPT Mode...")
        
    else:
        # Curated Topic
        topics = cosmos_orchestrator.load_json(cosmos_orchestrator.TOPICS_PATH, [])
        if args.topic_id:
            custom_topic = next((t for t in topics if t.get("id") == args.topic_id), None)
            if not custom_topic:
                print(f"[Warning] Topic ID {args.topic_id} not found. Selecting next available topic.")
                custom_topic = cosmos_orchestrator.get_next_topic()
        else:
            custom_topic = cosmos_orchestrator.get_next_topic()
            
        custom_topic["mode"] = "curated"
        print(f"🌟 Running in CURATED TOPIC Mode: {custom_topic.get('topic_hi')}...")

    # 2. Run Pipeline
    preferred_model = args.model if args.model else None
    result = cosmos_orchestrator.run_cosmos_short_pipeline(
        custom_topic=custom_topic,
        auto_upload=args.upload,
        preferred_model=preferred_model
    )
    
    print("\n==================================================")
    print("🎉 GENERATION SUMMARY:")
    print(f"  Title: {result['content'].get('title')}")
    print(f"  Video Path: {result['files']['video']}")
    print(f"  Thumbnail Path: {result['files']['thumbnail_png']}")
    print(f"  Duration: {result['qa_checks']['duration_seconds']:.1f}s")
    print(f"  Keywords Used: {result['content'].get('keywords')}")
    print("==================================================")

if __name__ == "__main__":
    main()
