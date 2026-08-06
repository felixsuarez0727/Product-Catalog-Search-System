"""
Requirement (brief, section 2 - Mini-harvester):
  "sparsuj producent_novagen_snapshot.html" -- the file is described as a
  realistic, inconsistent scraper dump: "nie każda karta ma te same pola".

Specific structural quirks planted in the file that a robust parser must
survive without crashing or silently dropping data:
  - a card with no <ul class="specs"> at all (Startery losowe do RT / NO-10110)
  - a card whose data-sku has a lowercase-L typo (data-sku="NO-103l6")
  - two cards with no CSV counterpart at all (NO-99999, NO-10500)
"""


class TestSnapshotStructure:

    def test_parses_all_eleven_cards(self, snapshot):
        assert len(snapshot) == 11

    def test_every_product_has_nonempty_sku(self, snapshot):
        for p in snapshot:
            assert p.get("sku"), f"Missing/empty SKU in parsed product: {p}"

    def test_skus_are_uppercased_for_matching_consistency(self, snapshot):
        for p in snapshot:
            assert p["sku"] == p["sku"].upper(), (
                f"SKU {p['sku']!r} not uppercased -- this will break exact "
                f"matching against the normalized (uppercased) catalog SKUs."
            )


class TestMissingFieldsHandledGracefully:

    def test_card_without_specs_list_does_not_crash_and_yields_empty_list(self, snapshot):
        starters = [p for p in snapshot if p["sku"] == "NO-10110"]
        assert len(starters) == 1
        specs = starters[0].get("specifications")
        assert specs == [], f"Expected empty specs list for card with no <ul class=specs>, got {specs!r}"


class TestTypoSkuPreservedAsIs:
    """
    The parser's job is to extract the SKU faithfully, typo and all --
    NOT to try to correct it. Correction (if any) belongs to the merge
    layer's fuzzy matching, not the parser.
    """

    def test_typo_sku_extracted_unmodified_aside_from_case(self, snapshot):
        skus = [p["sku"] for p in snapshot]
        assert "NO-103L6" in skus, (
            f"Expected the raw (typo'd) SKU 'NO-103L6' (from data-sku='NO-103l6') "
            f"to appear verbatim (just uppercased) in the parsed output. "
            f"Got these SKUs instead: {sorted(skus)}"
        )


class TestOutOfCatalogProductsStillParsed:
    """
    The brief explicitly says: 'nie zakładaj, że każda karta ma parę w CSV' --
    the parser must not filter cards based on whether they exist in the
    catalog (that decision belongs to the merge step, not the parser).
    """

    def test_new_product_card_parsed(self, snapshot):
        skus = [p["sku"] for p in snapshot]
        assert "NO-10500" in skus

    def test_discontinued_product_card_parsed(self, snapshot):
        skus = [p["sku"] for p in snapshot]
        assert "NO-99999" in skus


class TestDescriptionExtraction:

    def test_description_text_extracted_and_cleaned(self, snapshot):
        kit = next(p for p in snapshot if p["sku"] == "NO-10009")
        desc = kit.get("description")
        assert desc, "Description should not be empty for a card that has a <p class='product-desc'>"
        assert "\n" not in desc, "Whitespace/newlines from the raw HTML should be collapsed"
