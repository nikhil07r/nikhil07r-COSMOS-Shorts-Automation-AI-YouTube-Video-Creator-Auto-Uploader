import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))
import cosmos_orchestrator

def main():
    topics = cosmos_orchestrator.load_json(cosmos_orchestrator.TOPICS_PATH, [])
    # Find space_01 topic
    space_topic = next((t for t in topics if t.get("id") == "space_01"), None)
    if not space_topic:
        print("[Error] space_01 topic not found!")
        return

    print(f"Starting COSMOS Short generation for topic: {space_topic['topic_hi']}")
    result = cosmos_orchestrator.run_cosmos_short_pipeline(
        custom_topic=space_topic,
        auto_upload=False,
        subtitle_position="custom",
        custom_position=76.0
    )
    print("\nGeneration finished successfully!")
    print(f"Output Video: {result['files']['video']}")
    print(f"Thumbnail: {result['files']['thumbnail_png']}")
    print(f"QA Checks: {result['qa_checks']}")

if __name__ == "__main__":
    main()
