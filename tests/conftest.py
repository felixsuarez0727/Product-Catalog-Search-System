"""
Shared fixtures for the M1 assignment review test suite.

HOW TO USE
----------
Drop this whole `tests/` folder into the ROOT of the repo,
next to their `main.py` and `app/` package, so the structure looks like:

    <repo>/
        main.py
        app/
            config.py
            normalize.py
            parser.py
            merge.py
            embeddings.py
            search.py
        data/
            katalog_probka.csv
            producent_novagen_snapshot.html
        tests/              <-- this folder
            conftest.py
            test_normalize.py
            test_dedup.py
            test_parser.py
            test_merge.py
            test_search.py

Then, from the repo root, with the project's own virtualenv activated
(so their requirements.txt-pinned versions are used):

    pip install pytest
    pytest tests/ -v

The first run that touches `semantic_index` will download the
sentence-transformers model (all-MiniLM-L6-v2) if it isn't cached locally
yet -- that's expected and only happens once.

WHAT THIS SUITE ASSUMES
------------------------
- It imports directly from the project's own `app` package -- it does
  NOT reimplement or mock their normalize/parser/merge/search logic. If
  their module or function names differ from the ones referenced here,
  update the imports at the top of each test file accordingly (that
  itself is useful review signal).
- It reads the actual provided `data/katalog_probka.csv` and
  `data/producent_novagen_snapshot.html` -- no synthetic data is used for
  the "real data" tests. Small synthetic fixtures are used only in tests
  that need a controlled scenario (see test_dedup.py, test_merge.py,
  test_search.py) to isolate a single behavior.

WHY SOME TESTS ARE EXPECTED TO FAIL
------------------------------------
Several tests target scenarios the assignment brief explicitly plants:
  - near-duplicate/typo catalog numbers (SKU dedup)
  - a typo'd SKU in the manufacturer snapshot that should still match
    its catalog counterpart
  - filter (manufacturer/category) correctness after semantic search
A failing test in this suite is not necessarily a test bug -- it's
evidence about whether the submission handles a required scenario. Each
such test has a comment explaining exactly what behavior is being
checked and why it matters per the brief.
"""
from app.merge import merge_catalog_and_snapshot
from app.parser import parse_snapshot
from app.normalize import read_catalog, normalize_catalog, deduplicate_catalog
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# These imports assume the project's app package structure & function
# names as described in the assignment / their own README. Adjust here if
# their actual module differs.

try:
    from app.config import INPUT_FILE, SNAPSHOT_FILE
    CSV_PATH = os.path.join(PROJECT_ROOT, INPUT_FILE)
    SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, SNAPSHOT_FILE)
except ImportError:
    # Fall back to the paths given in the assignment brief if config.py
    # doesn't expose these constants under these names.
    CSV_PATH = os.path.join(PROJECT_ROOT, "data", "katalog_probka.csv")
    SNAPSHOT_PATH = os.path.join(
        PROJECT_ROOT, "data", "producent_novagen_snapshot.html")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "knownbug: test targets a scenario the brief requires; failure is review evidence, not a test defect"
    )


@pytest.fixture(scope="session")
def raw_catalog():
    assert os.path.exists(CSV_PATH), f"Catalog CSV not found at {CSV_PATH}"
    return read_catalog(CSV_PATH)


@pytest.fixture(scope="session")
def normalized_catalog(raw_catalog):
    return normalize_catalog(raw_catalog)


@pytest.fixture(scope="session")
def deduped_catalog(normalized_catalog):
    return deduplicate_catalog(normalized_catalog)


@pytest.fixture(scope="session")
def snapshot():
    assert os.path.exists(
        SNAPSHOT_PATH), f"Snapshot HTML not found at {SNAPSHOT_PATH}"
    return parse_snapshot(SNAPSHOT_PATH)


@pytest.fixture(scope="session")
def merged_catalog(deduped_catalog, snapshot):
    return merge_catalog_and_snapshot(deduped_catalog, snapshot)


@pytest.fixture(scope="session")
def semantic_index(merged_catalog):
    """
    Builds the REAL embedding index using the project's actual
    build_embeddings() and the real sentence-transformers model. This
    downloads/loads the model on first use -- expect this fixture to be
    slow (several seconds to ~1 min) the first time it's requested.
    """
    from app.embeddings import build_embeddings
    return build_embeddings(merged_catalog["catalog"])
