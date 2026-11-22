import re
from curl_cffi import requests

URL = "https://www.hdfilmcehennemi2.biz/dizi-izle/"
r = requests.get(
    URL,
    impersonate="chrome124",
    headers={"Accept-Language": "tr-TR,tr;q=0.9", "Referer": "https://www.google.com/"},
    timeout=20,
)
html = r.text

# loadMore fonksiyonunun veya x-data bloğunun etrafını yazdır
for keyword in ["loadMore", "Son Bölümler"]:
    idx = html.find(keyword)
    print(f"=== '{keyword}' BULUNDU MU?: {idx != -1} ===")
    if idx != -1:
        start = max(0, idx - 300)
        end = min(len(html), idx + 1200)
        print(html[start:end])
        print("\n" + "=" * 50 + "\n")
