import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.dirname(__file__))

import cosmos_youtube_uploader

COSMOS_DIR = os.path.dirname(__file__)
CLIENT_SECRET = os.path.join(COSMOS_DIR, "client_secret.json")
TOKEN = os.path.join(COSMOS_DIR, "token.json")

print("==================================================")
print("🔑 COSMOS YouTube Channel Authorization")
print("==================================================")
print("Opening your browser to authenticate with Google...")
print("Please select your YouTube channel account and click Allow.\n")

try:
    service = cosmos_youtube_uploader.get_youtube_service(CLIENT_SECRET, TOKEN)
    print("\n✅ Authorization successful! token.json has been created.")
    
    # Fetch channel name to verify
    channels_response = service.channels().list(mine=True, part="snippet").execute()
    items = channels_response.get("items", [])
    if items:
        ch_name = items[0]["snippet"]["title"]
        print(f"🎉 Connected Channel: {ch_name}")
    print("==================================================")
except Exception as e:
    print(f"\n❌ Error during authorization: {e}")
