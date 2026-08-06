# Product Catalog Search System

This project implements a complete product catalog processing pipeline for a laboratory products dataset.

The solution includes:

- catalog normalization
- duplicate resolution
- HTML snapshot parsing
- catalog merging
- semantic search using sentence embeddings
- an interactive command-line interface

The implementation was designed to satisfy all requirements described in the technical assignment while keeping the code modular and easy to extend.

---

## Technologies

The project was developed and tested using **Python 3.12** and the following libraries:

- **BeautifulSoup** – Parses the manufacturer HTML snapshot and extracts structured product information.
- **RapidFuzz** – Performs fuzzy SKU matching to identify and correct minor typographical errors during the merge process.
- **Sentence Transformers** – Generates semantic embeddings for products and user queries.
- **scikit-learn** – Performs cosine similarity search over the generated embeddings to implement semantic retrieval.
- **NumPy** – Provides efficient numerical array operations used by the embedding model and similarity search.
---

## Data Processing Pipeline

```
Catalog CSV
     │
     ▼
Normalize fields
     │
     ▼
Detect duplicate / near-duplicate SKUs
     │
     ▼
Validate product name similarity
     │
     ▼
Merge confirmed duplicates
     │
     ▼
Write normalized catalog
     │
     ▼
Parse manufacturer snapshot
     │
     ▼
Merge both data sources
     │
     ▼
Generate semantic embeddings
     │
     ▼
Interactive hybrid search
```

---

## Duplicate Resolution
Products are grouped by catalog number (SKU).

For duplicate entries:
- The most complete textual information is preserved.
- The lowest available price is selected.
- Missing values are filled from other duplicate records.
- A warning is logged when duplicate records contain different prices.

---

## Snapshot Merge

Products from the HTML snapshot are matched using the catalog number.

### Matching strategy

1. Exact SKU match.
2. Fuzzy SKU matching (RapidFuzz) to detect minor typographical errors.
3. Merge additional product information into the normalized catalog.

Products found only in the catalog remain available for search.
Products found only in the manufacturer snapshot are reported separately and are not automatically inserted into the catalog.

---

## Semantic Search
The search engine performs two different strategies.

### 1. Exact Search
If the query matches a catalog number exactly:

```
CH-10160
```

the corresponding product is immediately returned.

---

### 2. Semantic Search

Otherwise the query is converted into an embedding using

```
sentence-transformers/all-MiniLM-L6-v2
```

The embedding is compared against every product embedding using cosine similarity.

The best matches are returned together with

- similarity score
- relevance explanation

---

## Search Workflow

```
User query
     │
     ▼
    SKU?
     │
 ┌───┴─────────┐
 │             │
Yes           No
 │             │
 ▼             ▼
Exact      Embedding
Match          │
               ▼
      Cosine similarity
               │
               ▼
      Manufacturer filter
               │
               ▼
         Category filter
               │
               ▼
         Ranked results
```

---

## Prerequisites

- **Python 3.9–3.13**
     > **Note:** The project has been tested with Python 3.12. At the time of development, some dependencies (e.g. scikit-learn) were not yet compatible with Python 3.14.
- **Git**
---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 4. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 5. Install the project dependencies

```bash
pip install -r requirements.txt
```

> **Note (Windows):** Installing `sentence-transformers` (PyTorch) may fail on the first attempt due to Windows path length limitations (`WinError 206`). If this happens, simply rerun:
>
> ```bash
> pip install -r requirements.txt
> ```
>
> Alternatively, clone the project into a shorter path (e.g., `C:\dev\project`) or enable Windows long paths.

---

## Running

Run the application:

```bash
python main.py
```

The application provides an interactive command-line interface (CLI):

```text
============================================================
Hybrid Product Search
============================================================

1. Build search index
2. Search products
3. Exit
```

### Build Search Index

Option **1** executes the complete preprocessing pipeline:

- Normalize the catalog
- Detect and merge duplicate products
- Parse the manufacturer HTML snapshot
- Merge both data sources
- Generate semantic embeddings
- Build the search index

The search index is built once and can then be reused for multiple searches during the same execution.

---

### Search Products

Option **2** allows searching by catalog number (SKU) or natural language.

The user may also optionally filter the results by manufacturer and/or category.

```text
Search: PCR reagents
Manufacturer (optional):
Category (optional):
```

To return to the main menu:

```text
Search: back
```

---

## Example Searches

### Exact SKU search

```text
Search: CH-10160
```

Returns the exact matching product.

---

### Semantic search

```text
Search: DNA extraction kit
```

or

```text
Search: pH-metr stolowy
```

or

```text
Search: Laboratory plasticware
```

or

```text
Search: Master Mix do RT-PCR
```

---

### Search with manufacturer filter

```text
Search: PCR reagents
Manufacturer (optional): MedioScience
Category (optional):
```

Only products manufactured by **MedioScience** are returned.

---

### Search with category filter

```text
Search: laboratory
Manufacturer (optional):
Category (optional): laboratory plasticware
```

Only products belonging to the selected category are returned (None in this case).

---

### Search with both filters

```text
Search: Plytki 96-dolkowe
Manufacturer (optional): MedioScience
Category (optional): laboratory plasticware
```

Only products matching the semantic query and both filters are returned.

---

## Search Results

Each search result includes:

- SKU
- Product name (Polish)
- Manufacturer
- Category
- Relevance score
- Explanation of the match

---

## Running Tests

The project includes a test suite covering the main scenarios described in the assignment, including catalog normalization, duplicate and near-duplicate detection, HTML parsing, data merging, typo handling, hybrid search, and relevance scoring.

Install `pytest` and run the complete test suite:

```bash
pip install pytest
pytest -v
```

### Optional: Validate Similarity Thresholds

To reproduce the empirical validation of the SKU and name similarity thresholds on the complete catalog, run:

```bash
python validate_thresholds.py data/katalog_probka.csv
```

This utility analyzes the catalog and reports how the selected similarity thresholds behave across all product pairs, providing additional evidence that the chosen values correctly distinguish true duplicate/typo cases from unrelated products with similar catalog numbers.

---

## Notes

- **Product categories were normalized to a consistent English vocabulary** to improve filtering and semantic search.

- **Product names were intentionally preserved in their original language (Polish)** to avoid modifying the source data. The search index therefore operates on the original product names together with the normalized categories, manufacturer information, and any additional product details.

- The assignment suggests `FAISS` as a possible vector search backend. For this implementation, `scikit-learn` was chosen due to compatibility considerations and because the dataset is relatively small, where brute-force cosine similarity is sufficiently efficient. If the catalog were to grow significantly or support a high volume of concurrent similarity queries, a dedicated vector index such as `FAISS` would be the preferred solution.

---

## Future Improvements
To improve multilingual retrieval, the embedding model could be replaced with a multilingual Sentence Transformer (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) or product names or additional attributes could be translated during the normalization stage before generating embeddings.