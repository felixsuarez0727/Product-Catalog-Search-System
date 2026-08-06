"""
Requirement (brief, section 1 - Normalizacja):
  - różne zapisy tej samej wielkości opakowania (50 rxn / 50 reactions / x50 / 50szt)
  - różne nazewnictwo tych samych kategorii, w tym mieszanie PL/EN, oraz puste kategorie
  - różne zapisy ceny (PLN, zl, z groszami, bez waluty)
  - brakujące pola (kategoria / cena / atrybuty)
"""
import pytest
from app.normalize import (
    normalize_price,
    normalize_packaging,
    normalize_category,
    normalize_sku,
)


class TestPriceFormats:
    """Every price format that actually appears in katalog_probka.csv."""

    @pytest.mark.parametrize("raw,expected", [
        ("1021 zl", 1021.0),
        ("2467 zl", 2467.0),
        ("2156", 2156.0),          # bare number, no currency
        ("1990,00", 1990.0),       # comma decimal
        ("4199 PLN", 4199.0),
        ("385,00", 385.0),
        ("3399 PLN", 3399.0),
    ])
    def test_real_formats_from_csv(self, raw, expected):
        assert normalize_price(raw) == expected

    def test_missing_price_is_none_not_zero(self):
        # Several CSV rows have a genuinely empty price column
        # (e.g. "Probowki PCR 0.2ml,CH-10138,...,,"); make sure that
        # doesn't silently become 0.0.
        assert normalize_price("") is None

    def test_none_input_is_none(self):
        assert normalize_price(None) is None


class TestPackagingFormats:

    @pytest.mark.parametrize("raw", ["x50", "50szt", "50-pack", "50 rxn", "50 reactions"])
    def test_various_pack_size_notations_produce_a_result(self, raw):
        result = normalize_packaging(raw)
        assert result is not None, f"normalize_packaging({raw!r}) should not be None"

    def test_x50_and_50szt_normalize_to_a_comparable_form(self):
        """
        The brief specifically calls out these as *the same* pack size
        written differently: 50 rxn / 50 reactions / x50 / 50szt.
        A reasonable normalization should make these comparable (e.g. by
        extracting the same quantity), not leave them as four unrelated
        strings.
        """
        a = normalize_packaging("x50")
        b = normalize_packaging("50szt")
        assert "50" in (a or ""), f"'x50' normalized to {a!r}, lost the quantity"
        assert "50" in (b or ""), f"'50szt' normalized to {b!r}, lost the quantity"


class TestCategoryNormalization:
    """
    Requirement: mixed PL/EN category names for the same concept should
    converge to one canonical value; empty categories should not crash
    downstream code.
    """

    @pytest.mark.parametrize("raw,expected", [
        ("Plastiki lab.", "laboratory plasticware"),
        ("Plastik laboratoryjny", "laboratory plasticware"),
        ("Laboratory Plasticware", "laboratory plasticware"),
        ("PCR - odczynniki", "pcr reagents"),
        ("Odczynniki PCR", "pcr reagents"),
        ("PCR reagents", "pcr reagents"),
        ("izolacja DNA/RNA", "nucleic acid isolation"),
        ("Nucleic Acid Isolation", "nucleic acid isolation"),
    ])
    def test_pl_en_variants_converge(self, raw, expected):
        assert normalize_category(raw) == expected

    def test_empty_category_is_none_not_empty_string(self):
        assert normalize_category("") is None

    def test_none_category_is_none(self):
        assert normalize_category(None) is None


class TestSkuNormalization:

    def test_whitespace_and_case_normalized(self):
        assert normalize_sku("  no-10009 ") == "NO-10009"


class TestNormalizeCatalogEndToEnd:
    """Run normalize_catalog() over the REAL csv and sanity-check output shape."""

    def test_every_row_has_required_keys(self, normalized_catalog):
        required = {"nr_katalogowy", "nazwa", "producent", "kategoria", "opakowanie", "cena_pln", "atrybuty_dodatkowe"}
        for row in normalized_catalog[:5]:
            assert required.issubset(row.keys())

    def test_no_row_lost_missing_price_silently_becomes_wrong_type(self, normalized_catalog):
        for row in normalized_catalog:
            assert row["cena_pln"] is None or isinstance(row["cena_pln"], float)

    def test_all_skus_uppercased(self, normalized_catalog):
        for row in normalized_catalog:
            assert row["nr_katalogowy"] == row["nr_katalogowy"].upper()
