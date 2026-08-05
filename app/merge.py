from rapidfuzz import process
from .config import SIMILARITY_THRESHOLD_MERGE

def merge_catalog_and_snapshot(

    catalog: list[dict],
    snapshot: list[dict],
):

    snapshot_index = {
        p["sku"]: p
        for p in snapshot
    }

    matched_snapshot = set()
    enriched_catalog = []
    catalog_only = []

    for product in catalog:

        sku = product["nr_katalogowy"]

        snapshot_product = snapshot_index.get(sku)

        match_type = "exact"
        similarity = 100

        if snapshot_product is None:

            result = process.extractOne(
                sku,
                snapshot_index.keys(),
                score_cutoff=SIMILARITY_THRESHOLD_MERGE,
            )

            if result:

                matched_sku = result[0]
                similarity = result[1]
                snapshot_product = snapshot_index[matched_sku]
                match_type = "fuzzy"


        if snapshot_product:

            matched_snapshot.add(snapshot_product["sku"])
            enriched_catalog.append(
                {
                    **product,
                    "description": snapshot_product["description"],
                    "specifications": snapshot_product["specifications"],
                    "match_type": match_type,
                    "similarity": similarity,
                }
            )

        else:
            product["description"] = None
            product["specifications"] = []
            product["match_type"] = "catalog_only"
            product["similarity"] = None
            catalog_only.append(product)
            enriched_catalog.append(product)

    snapshot_only = []

    for product in snapshot:
        if product["sku"] not in matched_snapshot:
            product["match_type"] = "snapshot_only"
            snapshot_only.append(product)

    return {
        "catalog": enriched_catalog,
        "catalog_only": catalog_only,
        "snapshot_only": snapshot_only,
    }