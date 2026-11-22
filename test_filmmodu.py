from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://filmmodu.cc/yabanci-dizi-izle"

r = requests.get(
    URL,
    impersonate="chrome124",
    headers={"Accept-Language": "tr-TR,tr;q=0.9", "Referer": "https://www.google.com/"},
    timeout=20,
)
print(f"HTTP Durum Kodu: {r.status_code}")
soup = BeautifulSoup(r.text, "html.parser")

# 1. "Son Eklenen Yabancı Dizi Bölümleri" başlığını ve ilk 5 kartın ham HTML'ini bul
heading = soup.find(string=lambda t: t and "Son Eklenen Yabancı Dizi" in t)
if heading:
    section = heading.find_parent("section") or heading.find_parent("div").find_parent("div")
    links = section.find_all("a", href=True)
    print(f"Bölümde bulunan link sayısı: {len(links)}\n")
    for idx, a in enumerate(links[:5], 1):
        print(f"--- KART {idx} ---")
        print("METİN:", " | ".join(a.get_text(" | ", strip=True).split()))
        print("HTML:", str(a)[:500])
        print()
else:
    print("Başlık bulunamadı!")

# 2. "Daha Fazla Göster" butonunun HTML'ini incele
more_btn = soup.find(string=lambda t: t and "Daha Fazla" in t)
if more_btn:
    btn = more_btn.find_parent(["button", "a", "div"])
    print("--- DAHA FAZLA GÖSTER BUTONU ---")
    print(str(btn))
