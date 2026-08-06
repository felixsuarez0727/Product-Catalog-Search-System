"""
Requirement (brief, section 1 - Normalizacja):
  "Rozstrzygnij duplikaty/near-duplikaty numerów katalogowych - pokaż jak i dlaczego."

The provided katalog_probka.csv contains real examples of both:
  - exact duplicate SKUs (same catalog number repeated verbatim), e.g. PO-10022, CH-10160
  - near-duplicate/typo SKUs, e.g. PO-10093 / PO-10093A, BI-10220 / BI-10220-1

Both categories must be handled for this requirement to be satisfied --
only merging exact repeats is not "near-duplicate resolution".
"""
from app.normalize import deduplicate_catalog


def _row(sku, nazwa="Produkt", cena=100.0):
    return {
        "nr_katalogowy": sku,
        "nazwa": nazwa,
        "producent": "TestCo",
        "kategoria": "reagents",
        "opakowanie": "50 pcs",
        "cena_pln": cena,
        "atrybuty_dodatkowe": None,
    }


class TestExactDuplicates:

    def test_exact_repeated_sku_merges_to_one(self):
        rows = [_row("PO-10022", cena=1021.0), _row("PO-10022", cena=1021.0)]
        result = deduplicate_catalog(rows)
        assert len([r for r in result if r["nr_katalogowy"] == "PO-10022"]) == 1

    def test_lowest_price_kept_on_conflicting_duplicate_prices(self):
        rows = [_row("XX-1", cena=1021.0), _row("XX-1", cena=999.0)]
        result = deduplicate_catalog(rows)
        merged = next(r for r in result if r["nr_katalogowy"] == "XX-1")
        assert merged["cena_pln"] == 999.0


class TestNearDuplicateSkus:
    """
    Real near-duplicate pairs present in katalog_probka.csv.
    Each of these is a single-character SKU difference -- the minimal bar
    for "near-duplicate" handling described in the brief.
    """

    def test_po_10093_variants_merge(self, deduped_catalog):
        matches = [p["nr_katalogowy"] for p in deduped_catalog if p["nr_katalogowy"].startswith("PO-10093")]
        assert len(matches) == 1, (
            f"Expected PO-10093 and PO-10093A to resolve to a single product, "
            f"found {len(matches)} separate entries instead: {matches}. "
            f"If your near-duplicate matching only catches exact repeats, this "
            f"requirement isn't met."
        )

    def test_bi_10220_variants_merge(self, deduped_catalog):
        matches = [p["nr_katalogowy"] for p in deduped_catalog if p["nr_katalogowy"].startswith("BI-10220")]
        assert len(matches) == 1, (
            f"Expected BI-10220 and BI-10220-1 to resolve to a single product, "
            f"found {len(matches)} separate entries instead: {matches}."
        )

    def test_near_duplicate_isolated_scenario(self):
        """Same check, but isolated from the real CSV so it's easy to debug in isolation."""
        rows = [_row("PO-10093"), _row("PO-10093A")]
        result = deduplicate_catalog(rows)
        assert len(result) == 1


class TestDedupDoesNotOverMerge:
    """Sanity check the opposite failure mode: genuinely different SKUs must NOT be merged."""

    def test_unrelated_skus_stay_separate(self, deduped_catalog):
        no_9 = [p for p in deduped_catalog if p["nr_katalogowy"] == "NO-10009"]
        no_91 = [p for p in deduped_catalog if p["nr_katalogowy"] == "NO-10091"]
        assert len(no_9) == 1
        assert len(no_91) == 1
        # and they must not have been merged into one record under either key
        assert no_9[0]["nazwa"] != no_91[0]["nazwa"]


class TestFinalCatalogSizeIsReasonable:

    def test_deduped_catalog_smaller_than_raw(self, raw_catalog, deduped_catalog):
        assert len(deduped_catalog) < len(raw_catalog), (
            "Deduped catalog should be strictly smaller than the raw CSV row "
            "count, since the file contains deliberate exact duplicates."
        )

    def test_no_duplicate_skus_remain_in_final_output(self, deduped_catalog):
        skus = [p["nr_katalogowy"] for p in deduped_catalog]
        assert len(skus) == len(set(skus)), "Final deduped catalog still contains duplicate SKU keys"
