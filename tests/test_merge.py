"""
Requirement (brief, section 2 - Mini-harvester):
  "dopasuj po numerze katalogowym (nie po nazwie ...), zdecyduj co zrobić z
  pozycjami bez pary po żadnej stronie, opisz krótko jak obsłużyłeś/aś
  literówkę w SKU."

This is the single most important scenario in the whole assignment:
the manufacturer snapshot has one card with a typo'd SKU (data-sku=
"NO-103l6") that is clearly meant to correspond to catalog SKU "NO-10316"
(same product name "Izopropanol cz.d.a.", same manufacturer NovaGen Labs).
A correct submission must still match these two records despite the typo.
"""
import pytest
from app.merge import merge_catalog_and_snapshot


def _product(sku, **kwargs):
    base = {
        "nr_katalogowy": sku,
        "nazwa": "Produkt",
        "producent": "TestCo",
        "kategoria": "reagents",
        "opakowanie": "50 pcs",
        "cena_pln": 100.0,
        "atrybuty_dodatkowe": None,
    }
    base.update(kwargs)
    return base


def _snapshot_card(sku, name="Produkt", description="opis", specs=None):
    return {"sku": sku, "manufacturer_name": name, "description": description, "specifications": specs or []}


class TestExactSkuMatchSanity:
    """Baseline: exact SKU matches must work (this should always pass)."""

    def test_exact_match_enriches_catalog_product(self):
        catalog = [_product("NO-10009")]
        snap = [_snapshot_card("NO-10009", description="Kit RNA")]
        result = merge_catalog_and_snapshot(catalog, snap)
        assert result["catalog"][0]["description"] == "Kit RNA"


class TestTypoSkuMatching:
    """
    THE critical scenario. If this fails, the submission does not satisfy
    "opisz krótko jak obsłużyłeś/aś literówkę w SKU" in practice, whatever
    the README claims.
    """

    def test_isolated_typo_scenario(self):
        catalog = [_product("NO-10316", nazwa="Izopropanol cz.d.a.")]
        snap = [_snapshot_card("NO-103L6", name="Izopropanol cz.d.a.", description="Alkohol izopropylowy")]

        result = merge_catalog_and_snapshot(catalog, snap)

        assert len(result["snapshot_only"]) == 0, (
            "The typo'd snapshot SKU 'NO-103L6' was not matched to catalog "
            "SKU 'NO-10316' and was left in snapshot_only. Same product name "
            "('Izopropanol cz.d.a.'), same manufacturer -- this is exactly "
            "the typo scenario described in the assignment brief."
        )
        assert result["catalog"][0].get("description") == "Alkohol izopropylowy"

    def test_real_data_typo_scenario_end_to_end(self, deduped_catalog, snapshot):
        """Same check, run against the actual provided data files."""
        result = merge_catalog_and_snapshot(deduped_catalog, snapshot)
        unmatched_snapshot_skus = {p["sku"] for p in result["snapshot_only"]}
        assert "NO-103L6" not in unmatched_snapshot_skus, (
            f"NO-103L6 (typo for catalog SKU NO-10316) ended up unmatched in "
            f"snapshot_only. Full snapshot_only set: {unmatched_snapshot_skus}"
        )

    def test_matched_typo_product_has_fuzzy_match_type_if_field_exists(self, deduped_catalog, snapshot):
        result = merge_catalog_and_snapshot(deduped_catalog, snapshot)
        target = next((p for p in result["catalog"] if p["nr_katalogowy"] == "NO-10316"), None)
        assert target is not None, "NO-10316 missing from merged catalog entirely"
        if "match_type" in target:
            assert target["match_type"] in ("fuzzy", "exact"), (
                f"Expected NO-10316 to be matched (fuzzy or exact), got match_type={target.get('match_type')!r}"
            )


class TestOrphanHandling:
    """
    Requirement: decide what happens to items with no pair on either side,
    and don't silently drop them.
    """

    def test_snapshot_only_products_reported_not_silently_dropped(self, deduped_catalog, snapshot):
        result = merge_catalog_and_snapshot(deduped_catalog, snapshot)
        snapshot_only_skus = {p["sku"] for p in result["snapshot_only"]}
        # NO-99999 (discontinued/out-of-catalog) and NO-10500 (brand new
        # product) genuinely have no CSV counterpart and must surface here.
        assert "NO-99999" in snapshot_only_skus
        assert "NO-10500" in snapshot_only_skus

    def test_catalog_only_products_not_dropped_from_final_catalog(self, deduped_catalog, snapshot):
        result = merge_catalog_and_snapshot(deduped_catalog, snapshot)
        # Most catalog products have no snapshot card at all (snapshot only
        # covers ~11 of ~200+ products) -- they must still be searchable.
        assert len(result["catalog"]) == len(deduped_catalog), (
            "Products with no snapshot match should remain in the final "
            "catalog (with null description/specs), not be dropped."
        )

    def test_catalog_only_product_has_null_description_not_missing_key(self):
        catalog = [_product("XX-2")]
        result = merge_catalog_and_snapshot(catalog, [])
        assert "description" in result["catalog"][0]
        assert result["catalog"][0]["description"] is None
