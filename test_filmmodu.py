import cloudscraper
from bs4 import BeautifulSoup

URL = "https://filmmodu.cc/filmizle/turkce-dublaj-filmler-izle"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

print(f"İstek atılıyor: {URL}")
response = scraper.get(URL, timeout=20)
print(f"HTTP Durum Kodu: {response.status_code}")

if response.status_code != 200:
    print("Siteye ulaşılamadı veya engel (Cloudflare vb.) var.")
    print(response.text[:500])
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

# Sayfadaki film kartlarını yakalamak için genel ve güvenli arama
movies = []
for a in soup.find_all("a", href=True):
    text = " ".join(a.get_text(" | ", strip=True).split())
    # Kartlarda genelde "Dublaj" ve yıl/dk bilgisi geçer
    if "dk" in text and ("Dublaj" in text or "HD" in text or "4K" in text):
        movies.append((text, a["href"]))

# Tekrarları temizleyip sırayı koru
seen = set()
unique_movies = []
for title, href in movies:
    if href not in seen:
        seen.add(href)
        unique_movies.append((title, href))

print(f"\nBulunan film sayısı: {len(unique_movies)}\n")
for idx, (text, href) in enumerate(unique_movies[:15], 1):
    print(f"{idx}. {text}  -->  {href}")

# Eğer yukarıdaki filtre boş dönerse HTML yapısını görmek için örnek yazdır
if not unique_movies:
    print("\nSeçici eşleşmedi. HTML başlık/kart örneği:")
    print(soup.get_text(" | ", strip=True)[:1500])
