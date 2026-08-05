import logging

from app.config import (
    INPUT_FILE,
    OUTPUT_FILE,
    SNAPSHOT_FILE,
)

from app.normalize import (
    read_catalog,
    normalize_catalog,
    deduplicate_catalog,
    write_catalog,
)

from app.parser import parse_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)


def main():
    """
    Build the normalized catalog and semantic search index.
    """

    # Normalize catalog
    catalog = read_catalog(INPUT_FILE)

    logging.info(
        f"Normalize: Loaded {len(catalog)} catalog rows"
    )
    catalog = normalize_catalog(catalog)
    catalog = deduplicate_catalog(catalog)
    write_catalog(
        OUTPUT_FILE,
        catalog,
    )

    logging.info(
        f"Normalize: Catalog normalization finished"
        f" - {len(catalog)} unique products."
    )

    # Parse manufacturer snapshot
    snapshot = parse_snapshot(
        SNAPSHOT_FILE
    )
    logging.info(
        f"Parse: Parsed {len(snapshot)} products from snapshot"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated.")