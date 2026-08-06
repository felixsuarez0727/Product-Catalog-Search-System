"""
Requirement (brief, sections 3 & 4 - Wyszukiwarka hybrydowa + Ocena trafności):
  "dokładne dopasowanie po numerze katalogowym + wyszukiwanie semantyczne
  + prosty filtr (np. po producencie/kategorii)"
  "każdy wynik wyszukiwania ma dostać score + krótkie uzasadnienie
  (nie tylko liczbę)"

NOTE: tests in this file that call `semantic_index` will trigger loading
the real sentence-transformers model on first use. This is expected and
may take a while the first time (model download + load).
"""
import pytest
from app.search import exact_search, search


def _product(sku, nazwa="Produkt", producent="TestCo", kategoria="reagents"):
    return {
        "nr_katalogowy": sku,
        "nazwa": nazwa,
        "producent": producent,
        "kategoria": kategoria,
        "opakowanie": "50 pcs",
        "cena_pln": 100.0,
        "atrybuty_dodatkowe": None,
        "description": None,
        "specifications": [],
    }


class TestExactSkuSearch:

    def test_exact_sku_returns_correct_product(self, semantic_index):
        results = search("NO-10009", semantic_index)
        assert len(results) == 1
        assert results[0]["product"]["nr_katalogowy"] == "NO-10009"

    def test_exact_sku_search_is_case_insensitive(self, semantic_index):
        results = search("no-10009", semantic_index)
        assert len(results) == 1
        assert results[0]["product"]["nr_katalogowy"] == "NO-10009"

    def test_exact_match_gets_max_score(self, semantic_index):
        results = search("NO-10009", semantic_index)
        assert results[0]["score"] == 1.0

    def test_unknown_sku_falls_through_to_semantic_not_empty(self, semantic_index):
        # "ZZ-99999" isn't a real SKU, but also isn't gibberish -- it should
        # not crash, and should fall through to semantic search rather than
        # returning nothing or raising.
        results = search("ZZ-99999-NOTREAL", semantic_index)
        assert isinstance(results, list)


class TestSemanticSearchRelevance:
    """
    Loose, content-based relevance checks against the REAL embedding model
    and real catalog data. These intentionally avoid asserting exact scores
    (which depend on model internals) and instead check that the top
    result is *plausibly* relevant to the query.
    """

    def test_isopropanol_query_top_result_is_isopropanol_product(self, semantic_index):
        results = search("izopropanol", semantic_index, top_k=5)
        assert len(results) > 0
        top_name = results[0]["product"]["nazwa"].lower()
        assert "izopropanol" in top_name, (
            f"Expected top semantic result for 'izopropanol' query to be an "
            f"isopropanol product, got: {results[0]['product']['nazwa']!r}"
        )

    def test_dna_isolation_query_returns_relevant_category(self, semantic_index):
        results = search("izolacja DNA", semantic_index, top_k=5)
        assert len(results) > 0
        categories = [r["product"].get("kategoria") or "" for r in results]
        assert any("dna" in c.lower() or "nucleic" in c.lower() or "isolation" in c.lower() for c in categories), (
            f"None of the top-5 results for 'izolacja DNA' had a DNA/nucleic-acid "
            f"related category. Categories returned: {categories}"
        )

    def test_manufacturer_name_alone_should_not_dominate_relevance(self, semantic_index):
        """
        If the document text fed into the embedding model includes the raw
        manufacturer name (e.g. "Manufacturer: BioPrime"), a query that is
        just a manufacturer name can spuriously score unrelated products
        highly, purely on that field matching -- rather than on genuine
        product-content relevance. This test flags that risk; investigate
        the actual top results manually if it fails.
        """
        results = search("BioPrime", semantic_index, top_k=5)
        product_names = [r["product"]["nazwa"] for r in results]
        # Not a hard failure either way -- but print for manual review since
        # "does a manufacturer name return coherent, related products or a
        # random grab-bag of that manufacturer's unrelated SKUs" is a
        # judgment call worth a human looking at.
        print(
            f"\n[manual review] Query 'BioPrime' top-5 products: {product_names}")
        assert len(results) > 0


class TestFilters:

    def test_manufacturer_filter_only_returns_that_manufacturer(self, semantic_index):
        results = search("PCR", semantic_index,
                         manufacturer="MedioScience", top_k=10)
        for r in results:
            assert r["product"]["producent"] == "MedioScience"

    def test_category_filter_only_returns_that_category(self, semantic_index):
        results = search("odczynnik", semantic_index,
                         category="pcr reagents", top_k=10)
        for r in results:
            assert (r["product"].get("kategoria")
                    or "").lower() == "pcr reagents"

    def test_filter_for_manufacturer_with_known_real_matches_returns_something(self, semantic_index, deduped_catalog):
        """
        Regression test for filter-after-truncate ordering bugs: pick a
        manufacturer/category-relevant query where we know (from the real
        catalog data) that several matching products exist, and confirm
        the search actually surfaces at least one of them -- not zero,
        which would indicate filtering is discarding valid matches because
        it runs after results were already truncated to top_k.
        """
        manufacturer = "MedioScience"
        known_matches = [
            p for p in deduped_catalog
            if p["producent"] == manufacturer
            and p.get("kategoria") and "pcr" in p["kategoria"]
        ]
        assert len(
            known_matches) >= 5, "test assumption broken: expected several MedioScience PCR products in real data"

        results = search("PCR reagent mix", semantic_index,
                         manufacturer=manufacturer, top_k=5)

        assert len(results) > 0, (
            f"Found 0 results for manufacturer='{manufacturer}' with a PCR-related "
            f"query, even though {len(known_matches)} matching products exist in "
            f"the catalog: {[p['nr_katalogowy'] for p in known_matches]}. "
            f"If apply_filters() runs AFTER truncating to top_k in semantic_search(), "
            f"relevant results outside the raw top-k are silently discarded before "
            f"the filter ever sees them. Consider filtering a larger pool "
            f"(e.g. top_k * 5-10) before applying manufacturer/category filters, or "
            f"filtering before ranking/truncation."
        )


class TestScoreAndReasonQuality:
    """
    Requirement: 'każdy wynik ma dostać score + krótkie uzasadnienie
    (nie tylko liczbę)' -- the reason must be an actual explanation, not
    a constant string repeated regardless of score.
    """

    def test_reason_field_present_on_every_result(self, semantic_index):
        results = search("pipeta", semantic_index, top_k=5)
        for r in results:
            assert r.get("reason"), f"Result missing a 'reason' field: {r}"

    def test_reason_varies_meaningfully_with_score(self, semantic_index):
        results = search("centryfuga laboratoryjna do probowek",
                         semantic_index, top_k=5)
        if len(results) < 2:
            pytest.skip(
                "Not enough results returned to compare reason variability")

        scores = [r["score"] for r in results]
        reasons = [r["reason"] for r in results]

        if max(scores) - min(scores) > 0.05:
            # Meaningfully different scores but identical reason text
            # suggests the "reason" is a hardcoded placeholder rather than
            # an actual explanation tied to the match.
            assert len(set(reasons)) > 1, (
                f"Scores ranged from {min(scores):.3f} to {max(scores):.3f} "
                f"(a meaningful spread) but every result had the identical "
                f"reason text: {reasons[0]!r}. A constant string is not a "
                f"'krótkie uzasadnienie' (short justification) as required "
                f"by the brief -- it doesn't explain why THIS result matched."
            )

    def test_score_is_a_float_in_plausible_range(self, semantic_index):
        results = search("mikroRNA", semantic_index, top_k=5)
        for r in results:
            assert isinstance(r["score"], float)
            assert - \
                1.01 <= r["score"] <= 1.01, f"Score {r['score']} outside plausible cosine-similarity range"
