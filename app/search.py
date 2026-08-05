from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def exact_search(query, products):
    query = query.strip().upper()

    for product in products:
        if product["nr_katalogowy"].upper() == query:
            return product

    return None

def semantic_search(query, semantic_index, top_k=5):
    model = semantic_index["model"]
    embeddings = semantic_index["embeddings"]
    products = semantic_index["products"]

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    similarities = cosine_similarity(
        query_embedding,
        embeddings,
    )[0]

    ranked = np.argsort(similarities)[::-1][:top_k]

    results = []

    for idx in ranked:
        results.append({
            "product": products[idx],
            "score": float(similarities[idx]),
            "reason": "High semantic similarity."
        })

    return results

def apply_filters(results, manufacturer=None, category=None):
    filtered = []
    for result in results:
        product = result["product"]
        
        if manufacturer:
            prod_m = product.get("producent")
            if not prod_m or prod_m.lower() != manufacturer.lower():
                continue

        if category:
            prod_c = product.get("kategoria")
            if not prod_c or prod_c.lower() != category.lower():
                continue

        filtered.append(result)
    return filtered

def search(
    query,
    semantic_index,
    manufacturer=None,
    category=None,
    top_k=5,
):
    # 1. Exact SKU search
    product = exact_search(
        query,
        semantic_index["products"],
    )

    if product:
        return [{
            "product": product,
            "score": 1.0,
            "reason": "Exact catalog number match."
        }]

    # 2. Semantic search
    results = semantic_search(
        query,
        semantic_index,
        top_k,
    )

    # 3. Apply filters
    results = apply_filters(
        results,
        manufacturer,
        category,
    )
    return results