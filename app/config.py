# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
INPUT_FILE = "data/katalog_probka.csv"

OUTPUT_FILE = "data/standardized_catalog.csv"

SNAPSHOT_FILE = "data/producent_novagen_snapshot.html"

SIMILARITY_THRESHOLD_NORMALIZE = 85

SIMILARITY_THRESHOLD_MERGE = 85

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CATEGORY_MAP = {
    # Laboratory plasticware
    "plastiki lab.": "laboratory plasticware",
    "plastik laboratoryjny": "laboratory plasticware",
    "laboratory plasticware": "laboratory plasticware",

    # Measuring equipment
    "sprzet pomiarowy": "measuring equipment",
    "aparatura pomiarowa": "measuring equipment",
    "pomiary": "measuring equipment",
    "measuring equipment": "measuring equipment",

    # Disposable equipment
    "sprzet jednorazowy": "disposable equipment",
    "disposable equipment": "disposable equipment",

    # Reagents
    "odczynniki": "reagents",
    "reagents": "reagents",

    # Chemical reagents
    "odczynniki chemiczne": "chemical reagents",
    "chemia laboratoryjna": "chemical reagents",
    "chemicals": "chemical reagents",
    "chemical reagents": "chemical reagents",

    # PCR reagents
    "odczynniki do pcr": "pcr reagents",
    "odczynniki pcr": "pcr reagents",
    "pcr - odczynniki": "pcr reagents",
    "pcr reagents": "pcr reagents",

    # Nucleic acid isolation
    "izolacja dna": "nucleic acid isolation",
    "izolacja dna/rna": "nucleic acid isolation",
    "izolacja kwasow nukleinowych": "nucleic acid isolation",
    "nucleic acid isolation": "nucleic acid isolation",
}