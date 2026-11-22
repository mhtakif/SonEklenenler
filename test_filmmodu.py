from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://filmmodu.cc/diziler/bolum-veri"
HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://filmmodu.cc/yabanci-dizi-izle",
    "Origin": "https://filmmodu.cc",
    "X-Requested-With": "XMLHttpRequest",
}

tests = [
    ("POST data sayfa=2", {"data": {"sayfa": "2"}}),
    ("POST data page=2", {"data": {"page": "2"}}),
    ("POST json sayfa=2", {"json": {"sayfa": 2}}),
    ("POST url ?sayfa=2", {"params": {"sayfa": "2"}}),
]

for label, kwargs in tests:
    r = requests.post(URL, impersonate="chrome124", headers=HEADERS, timeout=20, **kwargs)
    print(f"=== {label} -> HTTP {r.status_code} | Uzunluk: {len(r.text)} ===")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("a.yd-mini")
        print(f"Bulunan kart sayısı: {len(cards)}")
        for a in cards[:3]:
            ad = a.select_one("b.yd-mini-ad")
            dublaj = "DUBLAJ" if a.find(attrs={"aria-label": "Türkçe Dublaj"}) else "Sadece Altyazı"
            print(f"  - {ad.get_text(strip=True) if ad else '?'} [{dublaj}]")
        if not cards:
            print("Ham çıktı örneği:", r.text[:250])
    else:
        print("Hata örneği:", r.text[:150])
    print()
