from curl_cffi import requests
from bs4 import BeautifulSoup

HEADERS = {"Accept-Language": "tr-TR,tr;q=0.9", "Referer": "https://filmmodu.cc/yabanci-dizi-izle"}

# 1. Kartların altındaki dil/bayrak rozetlerini gör
r = requests.get("https://filmmodu.cc/yabanci-dizi-izle", impersonate="chrome124", headers=HEADERS, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

print("=== DİL ROZETLERİ (İlk 2 ve Fire Country) ===")
for a in soup.select("a.yd-mini"):
    ad = a.select_one("b.yd-mini-ad").get_text(strip=True)
    alt = a.select_one("span.yd-mini-alt")
    if ad in ["Son Masa", "Vienna Game", "Fire Country", "FBI"]:
        print(f"{ad} --> {alt}\n")

# 2. Daha Fazla Göster (sayfa 2) test
for param in ["sayfa=2", "page=2"]:
    u = f"https://filmmodu.cc/diziler/bolum-veri?{param}"
    r2 = requests.get(u, impersonate="chrome124", headers=HEADERS, timeout=20)
    print(f"TEST {param} -> HTTP {r2.status_code} | Uzunluk: {len(r2.text)} | Örnek: {r2.text[:150]}")
