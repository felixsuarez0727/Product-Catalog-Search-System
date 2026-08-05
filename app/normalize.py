import csv
import logging
import re
from .config import CATEGORY_MAP, SIMILARITY_THRESHOLD_NORMALIZE
from collections import defaultdict
from rapidfuzz import fuzz

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def choose_best(values):
    """Return the most informative non-empty value."""
    values = [v for v in values if v not in ("", None)]
    if not values:
        return None
    return max(values, key=len)

def normalize_price(value):
    """Normalize different price formats into float."""

    if value is None or value.strip() == "":
        return None

    text = value.strip().lower()

    text = re.sub(r"pln|zl", "", text)
    text = text.replace(" ", "")

    if text.count(",") > 1 and "." not in text:
        text = text.replace(",", "")
    elif text.count(",") == 1 and "." not in text:
        text = text.replace(",", ".")
    elif "," in text and "." in text:
        text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        logging.warning(f"Normalize: Invalid price: {value}")
        return None


def normalize_packaging(value):
    """Normalize packaging notation."""

    if value is None:
        return None

    text = value.strip().lower()

    if text == "":
        return None

    replacements = {
        "szt.": "szt",
        "test.": "test",
        "reactions": "rxn",
        "op": "pkg",
        "pack": "pkg",
        "szt": "pcs",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    regex_rules = [
        (r"^x\s*(\d+)$", r"\1 pcs"),
        (r"^(\d+)-+$", r"\1 pcs"),
        (r"^(\d+)(pcs|pkg|rxn|test|kg|g|ml|l)$", r"\1 \2"),
        (r"^(\d+)\s*(pcs|pkg|rxn|test|kg|g|ml|l)$", r"\1 \2"),
        (r"\b(\d+)pcs\b", r"\1 pcs"),
        (r"\b(\d+)-pkg\b", r"\1 pkg"),
        (r"\b(\d+)szt\b", r"\1 pcs"),
        (r"\bx(\d+)\b", r"\1 pcs"),
    ]

    for pattern, replacement in regex_rules:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"\s+", " ", text).strip()

    if re.fullmatch(r"\d+", text):
        text += " pcs"

    return text


def normalize_category(value):
    """Normalize category names."""

    if value is None:
        return None

    text = value.strip().lower()

    if text == "":
        return None

    if text not in CATEGORY_MAP:
        logging.warning(f"Normalize: Unknown category: '{text}'")

    return CATEGORY_MAP.get(text, text)


def normalize_sku(value):
    return value.strip().upper()


def normalize_text(value):
    if value is None:
        return None

    value = value.strip()

    return value if value else None


# -----------------------------------------------------------------------------
# IO
# -----------------------------------------------------------------------------

def read_catalog(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_catalog(path, rows):
    fieldnames = [
        "nr_katalogowy",
        "nazwa",
        "producent",
        "kategoria",
        "opakowanie",
        "cena_pln",
        "atrybuty_dodatkowe",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# -----------------------------------------------------------------------------
# Normalization
# -----------------------------------------------------------------------------
def normalize_catalog(rows):
    normalized = []
    for row in rows:
        normalized.append(
            {
                "nr_katalogowy": normalize_sku(row["nr_katalogowy"]),
                "nazwa": normalize_text(row["nazwa"]),
                "producent": normalize_text(row["producent"]),
                "kategoria": normalize_category(row["kategoria"]),
                "opakowanie": normalize_packaging(row["opakowanie"]),
                "cena_pln": normalize_price(row["cena"]),
                "atrybuty_dodatkowe": normalize_text(
                    row["atrybuty_dodatkowe"]
                ),
            }
        )

    return normalized

# -----------------------------------------------------------------------------
# Deduplication
# -----------------------------------------------------------------------------
def group_similar_skus(rows):
    grouped = defaultdict(list)
    for row in rows:
        sku = row["nr_katalogowy"]
        # Exact duplicate
        if sku in grouped:
            grouped[sku].append(row)
            continue
        found = False
        for existing in grouped:
            score = fuzz.ratio(existing, sku)
            if score >= SIMILARITY_THRESHOLD_NORMALIZE:
                logging.info(
                    f"Normalize: Fuzzy SKU match: '{sku}' -> '{existing}' ({score:.1f})"
                )
                grouped[existing].append(row)
                found = True
                break
        if not found:
            grouped[sku].append(row)
    return grouped

def deduplicate_catalog(rows):
    grouped = group_similar_skus(rows)
    deduped = []
    for sku, group in grouped.items():
        if len(group) > 1:
            logging.info(
                f"Normalize: Found {len(group)} duplicate records for {sku}"
            )
        prices = [
            r["cena_pln"]
            for r in group
            if r["cena_pln"] is not None
        ]
        if len(set(prices)) > 1:
            logging.warning(
                f"Normalize: Different prices for {sku}: {prices}"
            )
        merged = {
            "nr_katalogowy": sku,
            "nazwa": choose_best(
                [r["nazwa"] for r in group]
            ),
            "producent": choose_best(
                [r["producent"] for r in group]
            ),
            "kategoria": choose_best(
                [r["kategoria"] for r in group]
            ),
            "opakowanie": choose_best(
                [r["opakowanie"] for r in group]
            ),
            "cena_pln": min(prices) if prices else None,
            "atrybuty_dodatkowe": choose_best(
                [r["atrybuty_dodatkowe"] for r in group]
            ),
        }
        deduped.append(merged)
    return deduped