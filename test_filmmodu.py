from curl_cffi import requests
from bs4 import BeautifulSoup

session = requests.Session(impersonate="chrome124")
HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://filmmodu.cc/yabanci-dizi-izle",
    "Origin": "https://filmmodu.cc",
}

# 1. Önce ana sayfayı açıp çerezi ve CSRF token'ı al
r1 = session.get("https://filmmodu.cc/yabanci-dizi-izle", headers=HEADERS, timeout=20)
soup1 = BeautifulSoup(r1.text, "html.parser")
meta = soup1.find("meta", attrs={"name": "csrf-token"})
csrf = meta["content"] if meta else ""
print(f"CSRF Token bulundu mu?: {'EVET' if csrf else 'HAYIR'}")

# 2. Token ve çerez ile POST isteği at
post_headers = {
    **HEADERS,
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRF-TOKEN": csrf,
}

for key in ["sayfa", "page"]:
    r2 = session.post(
        "https://filmmodu.cc/diziler/bolum-veri",
        headers=post_headers,
        data={key: "2"},
        timeout=20,
    )
    print(f"=== POST {key}=2 -> HTTP {r2.status_code} | Uzunluk: {len(r2.text)} ===")
    if r2.status_code == 200:
        soup2 = BeautifulSoup(r2.text, "html.parser")
        cards = soup2.select("a.yd-mini")
        print(f"Bulunan kart sayısı: {len(cards)}")
        for a in cards[:4]:
            ad = a.select_one("b.yd-mini-ad")
            dublaj = "DUBLAJ" if a.find(attrs={"aria-label": "Türkçe Dublaj"}) else "Sadece Altyazı"
            print(f"  - {ad.get_text(strip=True) if ad else '?'} [{dublaj}]")
        if not cards:
            print("Ham çıktı örneği:", r2.text[:250])
    print()
