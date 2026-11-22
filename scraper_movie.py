import os
import re
import json
import time
from itertools import zip_longest
from curl_cffi import requests
from bs4 import BeautifulSoup

TMDB_TOKEN = os.environ.get("TMDB_TOKEN", "").strip()
CATALOG_PATH = "catalog/movie/son_eklenen_filmler.json"
MIN_YEAR = 2021
MAX_ITEMS = 500

HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}


def fetch_html(url):
    try:
        r = requests.get(url, impersonate="chrome124", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            return r.text
        print(f"[UYARI] {url} -> HTTP {r.status_code}")
    except Exception as e:
        print(f"[HATA] {url} -> {e}")
    return None


def extract_year(parts):
    for i, p in enumerate(parts):
        m = re.fullmatch(r"(19\d{2}|20\d{2})", p.strip())
        if m:
            return int(m.group(1)), i
    return None, -1


def scrape_filmmodu():
    html = fetch_html("https://filmmodu.cc/filmizle/turkce-dublaj-filmler-izle")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href in seen:
            continue
        text = " ".join(a.get_text(" | ", strip=True).split())
        if "dk" in text and ("Dublaj" in text or "HD" in text or "4K" in text):
            seen.add(href)
            parts = [p.strip() for p in text.split("|")]
            year, y_idx = extract_year(parts)
            if year and y_idx >= 2:
                results.append({
                    "tr_title": parts[y_idx - 2],
                    "orig_title": parts[y_idx - 1],
                    "year": year,
                    "source": "filmmodu",
                })
    print(f"Filmmodu (Film): {len(results)} bulundu")
    return results


def scrape_setfilmizle():
    html = fetch_html("https://www.setfilmizle.ltd/turkce-dublaj-filmler/")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for card in soup.select("article, .item, .movie-item, .film-box, .poster"):
        a = card.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if href in seen or href.rstrip("/").endswith("/film"):
            continue
        text = " ".join(card.get_text(" | ", strip=True).split())
        if "Yıl" not in text:
            continue
        seen.add(href)
        parts = [p.strip() for p in text.split("|")]
        year, title = None, ""
        if "Yıl" in parts:
            idx = parts.index("Yıl")
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                year = int(parts[idx + 1])
        if "IMDb" in parts:
            idx = parts.index("IMDb")
            if idx >= 1:
                title = parts[idx - 1]
        if title and year:
            results.append({
                "tr_title": title,
                "orig_title": "",
                "year": year,
                "source": "setfilmizle",
            })
    print(f"Setfilmizle (Film): {len(results)} bulundu")
    return results


def scrape_hdfilmdelisi():
    html = fetch_html("https://hdfilmdelisi1.com/film-kesfet?dil=dublaj")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for card in soup.select("article, .item, .movie-item, .film-box, .poster, .card"):
        a = card.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if href in seen or "/film/" not in href:
            continue
        text = " ".join(card.get_text(" | ", strip=True).split())
        parts = [p.strip() for p in text.split("|")]
        year, _ = extract_year(parts)
        if year and len(parts) >= 2:
            seen.add(href)
            results.append({
                "tr_title": parts[0],
                "orig_title": parts[1],
                "year": year,
                "source": "hdfilmdelisi",
            })
    print(f"HDFilmDelisi (Film): {len(results)} bulundu")
    return results


def scrape_hdfilmcehennemi():
    html = fetch_html("https://www.hdfilmcehennemi2.biz/turkce-dublaj/")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    results, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href in seen or any(x in href for x in ["/tur/", "/kategori/", "/dizi-izle/"]):
            continue
        text = " ".join(a.get_text(" | ", strip=True).split())
        parts = [p.strip() for p in text.split("|")]
        if len(parts) >= 4 and parts[-1] == "Film":
            year, _ = extract_year(parts)
            title = parts[-2]
            if year and title:
                seen.add(href)
                results.append({
                    "tr_title": title,
                    "orig_title": "",
                    "year": year,
                    "source": "hdfilmcehennemi",
                })
    print(f"HDFilmCehennemi (Film): {len(results)} bulundu")
    return results


def tmdb_get(endpoint, params=None):
    url = f"https://api.themoviedb.org/3{endpoint}"
    headers = {"Authorization": f"Bearer {TMDB_TOKEN}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    return r.json() if r.status_code == 200 else None


def resolve_tmdb_meta(item):
    queries = []
    if item["orig_title"]:
        queries.append(item["orig_title"])
    if item["tr_title"] and item["tr_title"] not in queries:
        queries.append(item["tr_title"])

    tmdb_id = None
    for q in queries:
        data = tmdb_get("/search/movie", {"query": q, "year": item["year"], "language": "tr-TR"})
        if data and data.get("results"):
            tmdb_id = data["results"][0]["id"]
            break
        data = tmdb_get("/search/movie", {"query": q, "language": "tr-TR"})
        if data and data.get("results"):
            for res in data["results"][:3]:
                rel = res.get("release_date", "")[:4]
                if rel.isdigit() and abs(int(rel) - item["year"]) <= 1:
                    tmdb_id = res["id"]
                    break
        if tmdb_id:
            break

    if not tmdb_id:
        return None

    details = tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "external_ids", "language": "tr-TR"})
    if not details:
        return None

    imdb_id = details.get("imdb_id") or details.get("external_ids", {}).get("imdb_id")
    if not imdb_id or not imdb_id.startswith("tt"):
        return None

    release_year_str = (details.get("release_date") or str(item["year"]))[:4]
    if release_year_str.isdigit() and int(release_year_str) < MIN_YEAR:
        return None

    meta = {
        "id": imdb_id,
        "type": "movie",
        "name": details.get("title") or item["tr_title"],
        "releaseInfo": release_year_str,
        "imdbRating": f"{details.get('vote_average', 0):.1f}",
        "genres": [g["name"] for g in details.get("genres", [])],
        "description": details.get("overview") or "",
    }
    if details.get("poster_path"):
        meta["poster"] = f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
    if details.get("backdrop_path"):
        meta["background"] = f"https://image.tmdb.org/t/p/original{details['backdrop_path']}"
    if details.get("runtime"):
        meta["runtime"] = f"{details['runtime']} dk"
    return meta


def main():
    if not TMDB_TOKEN:
        raise SystemExit("TMDB_TOKEN ortam değişkeni bulunamadı!")

    existing_metas = []
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            existing_metas = json.load(f).get("metas", [])

    existing_ids = {m["id"] for m in existing_metas}

    site_lists = [
        scrape_filmmodu(),
        scrape_setfilmizle(),
        scrape_hdfilmdelisi(),
        scrape_hdfilmcehennemi(),
    ]

    combined = []
    for group in zip_longest(*site_lists):
        for item in group:
            if item and item["year"] >= MIN_YEAR:
                combined.append(item)

    new_metas, new_ids = [], set()
    for item in combined:
        meta = resolve_tmdb_meta(item)
        if not meta or meta["id"] in existing_ids or meta["id"] in new_ids:
            continue
        new_ids.add(meta["id"])
        new_metas.append(meta)
        print(f"[YENİ FİLM] {meta['name']} ({meta['releaseInfo']}) - {meta['id']} [{item['source']}]")
        time.sleep(0.15)

    final_metas = (new_metas + existing_metas)[:MAX_ITEMS]
    os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"metas": final_metas}, f, ensure_ascii=False, indent=2)

    print(f"\nFilmler tamamlandı! Yeni: {len(new_metas)} | Toplam: {len(final_metas)}")


if __name__ == "__main__":
    main()
