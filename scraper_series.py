import os
import re
import json
import time
from itertools import zip_longest
from curl_cffi import requests
from bs4 import BeautifulSoup

TMDB_TOKEN = os.environ.get("TMDB_TOKEN", "").strip()
CATALOG_PATH = "catalog/series/son_eklenen_diziler.json"
MIN_YEAR = 2021
MAX_ITEMS = 500
FILMMODU_PAGES = 3  # 1. sayfa + 2 kez "Daha Fazla Göster"


def scrape_filmmodu_series():
    session = requests.Session(impersonate="chrome124")
    headers = {
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://filmmodu.cc/yabanci-dizi-izle",
        "Origin": "https://filmmodu.cc",
    }

    results, seen = [], set()
    try:
        r1 = session.get("https://filmmodu.cc/yabanci-dizi-izle", headers=headers, timeout=25)
        if r1.status_code != 200:
            print(f"[UYARI] Filmmodu Dizi -> HTTP {r1.status_code}")
            return []

        soup1 = BeautifulSoup(r1.text, "html.parser")
        meta = soup1.find("meta", attrs={"name": "csrf-token"})
        csrf = meta["content"] if meta else ""

        def parse_cards(soup):
            for a in soup.select("a.yd-mini"):
                if not a.find(attrs={"aria-label": "Türkçe Dublaj"}):
                    continue
                ad_el = a.select_one("b.yd-mini-ad")
                if not ad_el:
                    continue
                title = ad_el.get_text(strip=True)
                key = title.lower()
                if title and key not in seen:
                    seen.add(key)
                    results.append({"title": title, "year": None, "source": "filmmodu"})

        parse_cards(soup1)

        if csrf:
            post_headers = {**headers, "X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": csrf}
            for page in range(2, FILMMODU_PAGES + 1):
                r_more = session.post(
                    "https://filmmodu.cc/diziler/bolum-veri",
                    headers=post_headers,
                    data={"sayfa": str(page)},
                    timeout=20,
                )
                if r_more.status_code == 200:
                    parse_cards(BeautifulSoup(r_more.text, "html.parser"))
                time.sleep(0.3)
    except Exception as e:
        print(f"[HATA] Filmmodu Dizi -> {e}")

    print(f"Filmmodu (Dizi - Dublaj): {len(results)} benzersiz dizi bulundu")
    return results


def scrape_hdfilmcehennemi_series():
    headers = {"Accept-Language": "tr-TR,tr;q=0.9", "Referer": "https://www.google.com/"}
    results, seen = [], set()
    try:
        r = requests.get("https://www.hdfilmcehennemi2.biz/dizi-izle/", impersonate="chrome124", headers=headers, timeout=25)
        if r.status_code != 200:
            print(f"[UYARI] HDFilmCehennemi Dizi -> HTTP {r.status_code}")
            return []

        m = re.search(r"episodes:\s*JSON\.parse\('([^']+)'\)", r.text)
        if not m:
            print("[UYARI] HDFilmCehennemi Dizi JSON bloğu bulunamadı")
            return []

        raw_str = m.group(1).replace('"', '\\"').replace("\\'", "'")
        episodes = json.loads(json.loads(f'"{raw_str}"'))

        for ep in episodes:
            badges = ep.get("language_badges") or []
            if "tr" not in badges:
                continue
            title = (ep.get("series_title") or "").strip()
            year_raw = str(ep.get("series_year") or "").strip()
            year = int(year_raw) if year_raw.isdigit() else None
            key = title.lower()
            if title and key not in seen:
                seen.add(key)
                results.append({"title": title, "year": year, "source": "hdfilmcehennemi"})
    except Exception as e:
        print(f"[HATA] HDFilmCehennemi Dizi -> {e}")

    print(f"HDFilmCehennemi (Dizi - Dublaj): {len(results)} benzersiz dizi bulundu")
    return results


def tmdb_get(endpoint, params=None):
    url = f"https://api.themoviedb.org/3{endpoint}"
    headers = {"Authorization": f"Bearer {TMDB_TOKEN}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    return r.json() if r.status_code == 200 else None


def resolve_tmdb_series(item):
    params = {"query": item["title"], "language": "tr-TR"}
    if item["year"]:
        params["first_air_date_year"] = item["year"]

    data = tmdb_get("/search/tv", params)
    tmdb_id = None
    if data and data.get("results"):
        tmdb_id = data["results"][0]["id"]
    elif item["year"]:
        data = tmdb_get("/search/tv", {"query": item["title"], "language": "tr-TR"})
        if data and data.get("results"):
            tmdb_id = data["results"][0]["id"]

    if not tmdb_id:
        return None

    details = tmdb_get(f"/tv/{tmdb_id}", {"append_to_response": "external_ids", "language": "tr-TR"})
    if not details:
        return None

    imdb_id = details.get("external_ids", {}).get("imdb_id")
    if not imdb_id or not imdb_id.startswith("tt"):
        return None

    first_air = (details.get("first_air_date") or "")[:4]
    if first_air.isdigit() and int(first_air) < MIN_YEAR:
        return None

    meta = {
        "id": imdb_id,
        "type": "series",
        "name": details.get("name") or item["title"],
        "releaseInfo": first_air or (str(item["year"]) if item["year"] else ""),
        "imdbRating": f"{details.get('vote_average', 0):.1f}",
        "genres": [g["name"] for g in details.get("genres", [])],
        "description": details.get("overview") or "",
    }
    if details.get("poster_path"):
        meta["poster"] = f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
    if details.get("backdrop_path"):
        meta["background"] = f"https://image.tmdb.org/t/p/original{details['backdrop_path']}"
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
        scrape_filmmodu_series(),
        scrape_hdfilmcehennemi_series(),
    ]

    combined = []
    for group in zip_longest(*site_lists):
        for item in group:
            if item:
                combined.append(item)

    new_metas, new_ids = [], set()
    for item in combined:
        meta = resolve_tmdb_series(item)
        if not meta or meta["id"] in existing_ids or meta["id"] in new_ids:
            continue
        new_ids.add(meta["id"])
        new_metas.append(meta)
        print(f"[YENİ DİZİ] {meta['name']} ({meta['releaseInfo']}) - {meta['id']} [{item['source']}]")
        time.sleep(0.15)

    final_metas = (new_metas + existing_metas)[:MAX_ITEMS]
    os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"metas": final_metas}, f, ensure_ascii=False, indent=2)

    print(f"\nDiziler tamamlandı! Yeni: {len(new_metas)} | Toplam: {len(final_metas)}")


if __name__ == "__main__":
    main()
