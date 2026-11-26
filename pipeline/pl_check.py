import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token()
body = json.dumps({"snippet": {"playlistId": "PLM9buLI-Epxo", "resourceId": {"kind": "youtube#video", "videoId": "F8PpK5hzYmM"}}}).encode()
try:
    with urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", data=body, method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}), timeout=60) as r:
        print("ADDED", r.status)
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:500])
