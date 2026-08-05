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
from app.merge import merge_catalog_and_snapshot
from app.embeddings import build_embeddings
from app.search import search

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

def interactive_search(semantic_index):
    """
    Simple CLI interface for hybrid search.
    """

    print("\n" + "=" * 60)
    print("Hybrid Product Search")
    print("Type 'back' to return to the main menu.")
    print("=" * 60)

    while True:

        try:
            query = input("\nSearch: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nReturning to main menu...")
            break

        if not query:
            continue

        if query.lower() == "back":
            print("Returning to main menu...")
            break

        manufacturer = input(
            "Manufacturer (optional): "
        ).strip()

        category = input(
            "Category (optional): "
        ).strip()

        results = search(
            query=query,
            semantic_index=semantic_index,
            manufacturer=manufacturer or None,
            category=category or None,
            top_k=5,
        )

        if not results:
            print("\nNo results found.")
            continue

        print(f"\nFound {len(results)} result(s)\n")

        for i, result in enumerate(results, start=1):

            product = result["product"]

            print("-" * 60)
            print(f"#{i}")
            print(f"SKU          : {product['nr_katalogowy']}")
            print(f"Name         : {product['nazwa']}")
            print(f"Manufacturer : {product['producent']}")
            print(f"Category     : {product['kategoria']}")
            print(f"Score        : {result['score']:.3f}")
            print(f"Reason       : {result['reason']}")

def build_search_index():
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

    # Merge
    merge_result = merge_catalog_and_snapshot(
        catalog,
        snapshot,
    )

    logging.info(
        f"Merge: Matched products: "
        f"{len(merge_result['catalog']) - len(merge_result['catalog_only'])}"
    )

    logging.info(
        f"Merge: Catalog only: "
        f"{len(merge_result['catalog_only'])}"
    )

    logging.info(
        f"Merge: Snapshot only: "
        f"{len(merge_result['snapshot_only'])}"
    )

    # Build embeddings
    semantic_index = build_embeddings(
        merge_result["catalog"]
    )

    logging.info(
        f"Embeddings: Indexed "
        f"{len(semantic_index['products'])} products."
    )

    return semantic_index

def main():

    semantic_index = None

    while True:

        print("\n" + "=" * 60)
        print("Product Catalog Build and Search")
        print("=" * 60)
        print("1. Build search index")
        print("2. Search products")
        print("3. Exit")

        option = input("\nSelect an option (number): ").strip()

        if option == "1":
            print()
            semantic_index = build_search_index()
            print("\nSearch index successfully built.")
        elif option == "2":
            if semantic_index is None:
                print(
                    "\nSearch index has not been built yet."
                )
                print(
                    "Please select option 1 first."
                )
                continue
            interactive_search(
                semantic_index
            )
        elif option == "3":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated.")