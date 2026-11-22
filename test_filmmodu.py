from curl_cffi import requests
from bs4 import BeautifulSoup

URL = "https://sinemacc.com/dil/turkce-dublaj/"

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
    print("Siteye ulaşılamadı veya bot engeli var:")
    print(response.text[:400])
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

movies = []
cards = soup.select("article, .item, .movie-item, .film-box, .poster, .card, li.film")

for card in cards:
    a_tag = card.find("a", href=True)
    if not a_tag:
        continue
    href = a_tag["href"]
    text = " ".join(card.get_text(" | ", strip=True).split())
    if text and len(text) > 3:
        movies.append((text, href))

if not movies:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(k in href for k in ["/film/", "/izle/", "-izle"]):
            text = " ".join(a.get_text(" | ", strip=True).split())
            if text and len(text) > 2:
                movies.append((text, href))

seen = set()
unique_movies = []
for text, href in movies:
    if href not in seen:
        seen.add(href)
        unique_movies.append((text, href))

print(f"\nBulunan film sayısı: {len(unique_movies)}\n")
for idx, (text, href) in enumerate(unique_movies[:15], 1):
    print(f"{idx}. {text}  -->  {href}")

if not unique_movies:
    print("\nKart bulunamadı. Sayfa metni örneği:")
    print(soup.get_text(" | ", strip=True)[:1500])
