import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import cosmos_orchestrator

def test_story_input():
    # User's story concept:
    story = "1977 में वैज्ञानिकों को अंतरिक्ष से 72 सेकंड का एक रहस्यमयी सिग्नल मिला जिसे 'Wow! Signal' कहा जाता है। यह सिग्नल इतना शक्तिशाली था कि वैज्ञानिक आज तक यह नहीं समझ पाए कि इसे किस एलियन सभ्यता ने भेजा था!"
    
    topic = {
        "id": "wow_signal_01",
        "mode": "story",
        "category": "Space",
        "custom_story": story
    }
    
    print("\n--- Testing Story Mode ---")
    content = cosmos_orchestrator.cosmos_generator.generate_cosmos_content(topic)
    print("Title:", content.get("title"))
    print("Script (Hindi):", content.get("script"))
    print("Keywords:", content.get("keywords"))
    print("Thumbnail Text:", content.get("thumbnail_text"))
    
def test_script_input():
    # User's exact written script:
    script = "क्या आप जानते हैं हमारे ब्रह्मांड में एक ऐसा ग्रह भी मौजूद है जहां कांच की बारिश होती है? नंबर 1: HD 189733b — यह गहरा नीला ग्रह देखने में पृथ्वी जैसा खूबसूरत लगता है। नंबर 2: लेकिन यहां 8700 किलोमीटर प्रति घंटे की रफ्तार से चलने वाली भयानक हवाएं सिलिकेट के नुकीले कणों को उड़ाती हैं। नंबर 3: यहां का तापमान 1000 डिग्री सेल्सियस से भी ज्यादा रहता है। क्या इंसान कभी ऐसे ग्रहों पर कदम रख पाएगा? कमेंट में बताएं!"
    
    topic = {
        "id": "glass_rain_01",
        "mode": "script",
        "category": "Space",
        "custom_script": script
    }
    
    print("\n--- Testing Exact Script Mode ---")
    content = cosmos_orchestrator.cosmos_generator.generate_cosmos_content(topic)
    print("Title:", content.get("title"))
    print("Script (Preserved):", content.get("script"))
    print("Keywords:", content.get("keywords"))
    print("Thumbnail Text:", content.get("thumbnail_text"))

if __name__ == "__main__":
    test_story_input()
    test_script_input()
