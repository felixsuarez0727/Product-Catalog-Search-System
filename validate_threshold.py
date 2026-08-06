"""
Validation script: checks whether SIMILARITY_THRESHOLD_NORMALIZE (SKU) and
NAME_SIMILARITY_THRESHOLD (product name) actually separate "should merge"
from "should NOT merge" cleanly across the FULL catalog -- not just the
4 pairs the test suite happens to check.

Usage:
    python validate_thresholds.py dane/katalog_probka.csv

What it does:
    1. Reads every row from the CSV.
    2. For every pair of rows whose SKUs are similar enough to be considered
       by group_similar_skus() at all (i.e. would even reach the name check),
       computes both the SKU fuzz.ratio and the name token_sort_ratio.
    3. Prints every such pair sorted by name score, so you can visually
       inspect where the gap is (or isn't).

Read the output for:
    - Is there a clean gap between pairs that are obviously the same
      product (typo'd SKU, same name) and pairs that are obviously
      different products (coincidentally similar SKU, different name)?
    - Does NAME_SIMILARITY_THRESHOLD = 70 fall inside that gap, or does
      it cut through a cluster of ambiguous cases?
    - Are there pairs with missing/empty names that need special handling?
"""
import csv
import sys
from itertools import combinations
from rapidfuzz import fuzz

SKU_THRESHOLD = 60  # loose net: show anything even remotely SKU-similar,
# so we can see the full landscape, not just >=85


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(path):
    rows = load_rows(path)
    print(f"Loaded {len(rows)} rows from {path}\n")

    pairs = []
    for a, b in combinations(rows, 2):
        sku_a = (a.get("nr_katalogowy") or "").strip().upper()
        sku_b = (b.get("nr_katalogowy") or "").strip().upper()
        if not sku_a or not sku_b or sku_a == sku_b:
            continue  # exact dup handled separately, not interesting here

        sku_score = fuzz.ratio(sku_a, sku_b)
        if sku_score < SKU_THRESHOLD:
            continue  # not even SKU-similar, irrelevant to this check

        name_a = (a.get("nazwa") or "").strip()
        name_b = (b.get("nazwa") or "").strip()
        name_score = fuzz.token_sort_ratio(name_a, name_b)

        pairs.append((sku_score, name_score, sku_a, sku_b, name_a, name_b))

    if not pairs:
        print("No SKU-similar pairs found above the threshold.")
        return

    # Sort by name score so the gap (if any) is visually obvious
    pairs.sort(key=lambda p: p[1])

    print(f"{'SKU score':>9}  {'Name score':>10}  {'SKU A':<14}{'SKU B':<14}  Name A / Name B")
    print("-" * 100)
    for sku_score, name_score, sku_a, sku_b, name_a, name_b in pairs:
        flag = ""
        if name_score == 0 and (not name_a or not name_b):
            flag = "  <-- MISSING NAME, check this edge case"
        print(f"{sku_score:9.1f}  {name_score:10.1f}  {sku_a:<14}{sku_b:<14}  {name_a!r} / {name_b!r}{flag}")

    scores = [p[1] for p in pairs]
    print("\n--- Summary ---")
    print(f"Total SKU-similar pairs found: {len(pairs)}")
    print(f"Name score range: {min(scores):.1f} - {max(scores):.1f}")
    print(f"Pairs with name_score < 70 (would be BLOCKED from merging): "
          f"{sum(1 for s in scores if s < 70)}")
    print(f"Pairs with name_score >= 70 (would be ALLOWED to merge): "
          f"{sum(1 for s in scores if s >= 70)}")
    print("\nManually inspect the pairs near the 70 cutoff above -- confirm the ones")
    print("just above 70 really are the same product, and the ones just below")
    print("really are different products.")

    # SKU score >= threshold real de producción
    relevant = [p for p in pairs if p[0] >= 85]
    print(
        f"\n--- Pares que SÍ llegan al gate de nombre en el código real (SKU>=85): {len(relevant)} ---")
    for sku_score, name_score, sku_a, sku_b, name_a, name_b in sorted(relevant, key=lambda p: p[1]):
        print(
            f"{sku_score:6.1f}  {name_score:6.1f}  {sku_a:<14}{sku_b:<14}  {name_a!r} / {name_b!r}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_thresholds.py <path-to-katalog_probka.csv>")
        sys.exit(1)
    main(sys.argv[1])
