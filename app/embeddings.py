from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer

from .config import MODEL_NAME

def build_document(product: dict) -> str:
    """
    Build the text representation used for embeddings.
    """

    return f"""
    SKU: {product["nr_katalogowy"]}
    Name: {product["nazwa"]}
    Manufacturer: {product["producent"]}
    Category: {product["kategoria"]}
    Description: {product.get("description") or ""}

    Specifications:
    {" ".join(product.get("specifications", []))}
    """.strip()


def build_embeddings(products: list[dict]):
    """
    Create embeddings and a nearest neighbors index.
    """

    model = SentenceTransformer(MODEL_NAME)

    documents = [build_document(p) for p in products]

    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    index = NearestNeighbors(
        metric="cosine",
        algorithm="brute"
    )

    index.fit(embeddings)

    return {
        "model": model,
        "index": index,
        "embeddings": embeddings,
        "products": products,
    }