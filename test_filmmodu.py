import cloudscraper
from bs4 import BeautifulSoup

URL = "https://www.fullhdfilmizlesene.now/filmizle/turkce-dublaj-filmler-1"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

print(f"İstek atılıyor: {URL}")
response = scraper.get(URL, timeout=20)
print(f"HTTP Durum Kodu: {response.status_code}")

if response.status_code != 200:
    print("Siteye ulaşılamadı veya bot engeli (Cloudflare vb.) var.")
    print(response.text[:600])
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

movies = []
# fullhdfilmizlesene kart yapısı genelde li.film içindedir
cards = soup.select("li.film")

if cards:
    for card in cards:
        a_tag = card.find("a", href=True)
        href = a_tag["href"] if a_tag else ""
        # Türkçe başlık, orijinal başlık, yıl, imdb vb. metinleri birleştir
        text = " ".join(card.get_text(" | ", strip=True).split())
        if text:
            movies.append((text, href))
else:
    # Eğer sınıf adı farklıysa genel /film/ linklerinden yakala
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/film/" in href and len(a.get_text(strip=True)) > 2:
            text = " ".join(a.get_text(" | ", strip=True).split())
            movies.append((text, href))

# Tekrarları temizleyip sırayı koru
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
