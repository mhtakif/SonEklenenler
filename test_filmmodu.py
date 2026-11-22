from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://www.hdfilmcehennemi2.biz/dizi-izle/"

r = requests.get(
    URL,
    impersonate="chrome124",
    headers={"Accept-Language": "tr-TR,tr;q=0.9", "Referer": "https://www.google.com/"},
    timeout=20,
)
soup = BeautifulSoup(r.text, "html.parser")

# 1. İçinde "Sezon" geçen kartları bul (Son Bölümler)
ep_links = [a for a in soup.find_all("a", href=True) if "Sezon" in a.get_text()]
print(f"Bulunan Son Bölüm kart sayısı: {len(ep_links)}\n")

for idx, a in enumerate(ep_links[:3], 1):
    print(f"--- BÖLÜM KARTI {idx} ---")
    print("METİN:", " | ".join(a.get_text(" | ", strip=True).split()))
    print("HTML:", str(a))
    print()

# 2. Tam olarak "Daha Fazla Yükle" butonunu bul
more_btn = soup.find(string=lambda t: t and "Daha Fazla Yükle" in t)
if more_btn:
    btn = more_btn.find_parent(["button", "a"])
    print("--- DAHA FAZLA YÜKLE BUTONU ---")
    print(str(btn))
else:
    print("Daha Fazla Yükle butonu bulunamadı!")
