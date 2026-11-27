import json, sys, urllib.request, urllib.error
sys.path.insert(0, "pipeline")
from upload import access_token
tok = access_token(); h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
NEW="qx0gmmxgi2E"; OLD="tyxgV1mJmP0"
desc = ("بسبوسة وزيكو قدام العقرب الذهبي، والصندوق بيتفتح عن خريطة بتشع نور أحمر\n"
 "الجزء 4 من مسلسل حكايات بسبوسة (قصص بسبوس) كرتون مصري بالعامية\n\n"
 "الموسيقى: Sneaky Adventure - Kevin MacLeod (incompetech.com)\nLicensed under Creative Commons: By Attribution 4.0\nhttps://creativecommons.org/licenses/by/4.0/\n"
 "#حكايات_بسبوسة #كرتون_مصري #Shorts #رسوم_متحركة #قصص_بسبوسة")
tags=["Shorts","بسبوسة","بسبوس","قصص بسبوس","مسلسل بسبوس","حكايات","حكايات بسبوسة","شورتس","قصص قطط","قطط"]
def call(method,url,body=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,method=method,headers=h,data=json.dumps(body).encode() if body else None),timeout=60)
        return r.status, r.read().decode()[:200]
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
B="https://www.googleapis.com/youtube/v3/videos"
print("SNIP", call("PUT",B+"?part=snippet",{"id":NEW,"snippet":{"title":"العقرب الذهبي يهاجم بسبوسة والصندوق يتفتح! 🦂🗝️ - الجزء 4","description":desc,"tags":tags,"categoryId":"24"}}))
print("STAT", call("PUT",B+"?part=status",{"id":NEW,"status":{"privacyStatus":"private","publishAt":"2026-11-27T18:00:00Z","selfDeclaredMadeForKids":False,"embeddable":True,"publicStatsViewable":True,"license":"youtube"}}))
print("DEL", call("DELETE",B+"?id="+OLD))
import time; time.sleep(6)
for i in (NEW,OLD):
    v=json.load(urllib.request.urlopen(urllib.request.Request(B+"?part=snippet,status&id="+i,headers=h),timeout=60))
    for it in v["items"]: print("READ",i,it["snippet"]["title"],it["status"]["privacyStatus"],it["status"].get("publishAt"),it["snippet"]["description"][:80].replace("\n"," | "))
    print("COUNT",i,len(v["items"]))
