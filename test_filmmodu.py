from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1"

print(f"İstek atılıyor: {URL}")
response = requests.get(
    URL,
    impersonate="chrome124",
    headers={
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
    },
    timeout=20,
)
print(f"HTTP Durum Kodu: {response.status_code}")

if response.status_code != 200:
    print("Yine engel var:")
    print(response.text[:400])
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
cards = soup.select("li.film")

movies = []
for card in cards:
    a_tag = card.find("a", href=True)
    href = a_tag["href"] if a_tag else ""
    text = " ".join(card.get_text(" | ", strip=True).split())
    if text:
        movies.append((text, href))

print(f"\nBulunan film sayısı: {len(movies)}\n")
for idx, (text, href) in enumerate(movies[:15], 1):
    print(f"{idx}. {text}  -->  {href}")
