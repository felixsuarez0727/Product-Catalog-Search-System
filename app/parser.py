import re
from bs4 import BeautifulSoup

def parse_snapshot(path: str) -> list[dict]:
    """Parse manufacturer snapshot HTML."""

    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    products = []

    for card in soup.select(".product-card"):

        specs = [
            li.get_text(" ", strip=True)
            for li in card.select("ul.specs li")
        ]

        description_el = card.select_one(".product-desc")
        description = re.sub(r"\s+", " ", description_el.get_text()).strip() if description_el else None

        products.append(
            {
                "sku": card.get("data-sku", "").strip().upper(),
                "manufacturer_name": card.select_one(".product-name").get_text(strip=True),
                "description": description,
                "specifications": specs,
            }
        )

    return products