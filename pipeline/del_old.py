import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token(); h = {"Authorization": f"Bearer {tok}"}
try:
    r = urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?id=Pkbs9jL3Kw8", method="DELETE", headers=h), timeout=60)
    print("DELETED", r.status)
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:300])
v = json.load(urllib.request.urlopen(urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=status&id=Pkbs9jL3Kw8", headers=h), timeout=60))
print("REMAINING", len(v["items"]))
