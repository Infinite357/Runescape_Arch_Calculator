import os
import re
import requests
from urllib.parse import quote

ARTEFACTS_PAGE = "Artefacts"
OUTPUT_FOLDER = os.path.join("templates", "items")
DATA_FOLDER = "data"
ITEMS_JSON_PATH = os.path.join(DATA_FOLDER, "items.json")

HEADERS = {
    "User-Agent": "ItemXPCalculator/0.1 open-source educational project by xero9053"
}

API_URL = "https://runescape.wiki/api.php"


def make_safe_id(item_name):
    safe = item_name.lower()
    safe = safe.replace("'", "")
    safe = safe.replace("&", "and")
    safe = re.sub(r"[^a-z0-9]+", "_", safe)
    safe = safe.strip("_")
    return safe


def get_linked_page_names_from_artefacts_page():
    """
    Pulls links from https://runescape.wiki/w/Artefacts using the MediaWiki API.

    This returns many linked pages, so we filter out obvious non-item pages.
    """
    names = []
    continue_token = None

    while True:
        params = {
            "action": "query",
            "format": "json",
            "prop": "links",
            "titles": ARTEFACTS_PAGE,
            "pllimit": "max"
        }

        if continue_token:
            params["plcontinue"] = continue_token

        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
        response.raise_for_status()

        data = response.json()
        pages = data["query"]["pages"]

        for page_id in pages:
            links = pages[page_id].get("links", [])

            for link in links:
                title = link["title"]

                # Skip wiki/admin/category/file/template/helper pages
                if ":" in title:
                    continue

                # Skip broad/general pages that are not actual item names
                skip_titles = {
                    "Archaeology",
                    "Archaeology collections",
                    "Archaeology training",
                    "Artefacts",
                    "Calculator:Archaeology/Restoring artefacts",
                    "Chronotes",
                    "Damaged artefact",
                    "Excavation hotspots",
                    "Materials",
                    "Museum",
                    "Restored artefact"
                }

                if title in skip_titles:
                    continue

                names.append(title)

        if "continue" not in data:
            break

        continue_token = data["continue"]["plcontinue"]

    # remove duplicates while preserving order
    seen = set()
    unique_names = []

    for name in names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    return unique_names


def download_item_icon(item_name):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Most RuneScape Wiki item icon files are Item name.png
    wiki_filename = item_name + ".png"
    encoded_filename = quote(wiki_filename)

    url = f"https://runescape.wiki/wiki/Special:FilePath/{encoded_filename}"

    response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=20)

    if response.status_code != 200:
        print(f"FAILED: {item_name} | HTTP {response.status_code}")
        return None

    content_type = response.headers.get("Content-Type", "")

    if "image" not in content_type:
        print(f"FAILED: {item_name} | Not an image. Content-Type: {content_type}")
        return None

    item_id = make_safe_id(item_name)
    output_path = os.path.join(OUTPUT_FOLDER, item_id + ".png")

    with open(output_path, "wb") as file:
        file.write(response.content)

    print(f"Downloaded: {item_name} -> {output_path}")

    return {
        "id": item_id,
        "name": item_name,
        "template": f"templates/items/{item_id}.png",
        "xp": 0
    }


def write_items_json(items):
    os.makedirs(DATA_FOLDER, exist_ok=True)

    import json

    with open(ITEMS_JSON_PATH, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2)

    print(f"\nWrote {len(items)} items to {ITEMS_JSON_PATH}")


def main():
    print("Pulling artefact names from RuneScape Wiki...")
    names = get_linked_page_names_from_artefacts_page()

    print(f"Found {len(names)} possible artefact names.")
    print("Downloading icons...\n")

    downloaded_items = []

    for name in names:
        item = download_item_icon(name)

        if item:
            downloaded_items.append(item)

    write_items_json(downloaded_items)


if __name__ == "__main__":
    main()