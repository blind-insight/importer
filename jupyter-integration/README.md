# Jupyter Notebook Integration with Blind Insight

This directory contains the integration components that allow data scientists to use Blind Insight data in Jupyter Notebooks for machine learning workflows.

## Overview (for non‑engineers)

What this gives you:
- Encrypted data stays encrypted in Blind Insight.
- You can run encrypted queries (filters, ranges, and aggregations like avg/count/min/max) via the Blind Proxy.
- The notebook shows two workflows:
  - **Encrypted**: Use encrypted aggregations (no row decryption) for analytics/classification demos.
  - **Plaintext (illustrative only)**: Decrypt data and run standard scikit-learn. Kept for comparison; not privacy-preserving.

How it works:
- Jupyter → Python client → Backend `/api/blind/query` → Blind Proxy CLI → Blind Insight.
- Aggregations (avg/count/min/max, numeric ranges) are computed inside Blind Insight; only the aggregate values return.
- For encrypted examples, no raw rows are decrypted.

## Architecture

```
Jupyter Notebook
    ↓
Python Client (blind_insight_client.py)
    ↓
Backend API (/api/blind/query)
    ↓
Blind Proxy CLI
    ↓
Blind Insight (encrypted data)
```

## Setup

### 1) Prerequisites
- Blind Proxy installed and logged in (keyring initialized).
  ```bash
  ./blind organization list
  ./blind keyring inspect   # should show credentials
  ```
- Data uploaded to Blind Insight (e.g., Iris) with:
  - `species` labels
  - `dataset-order` field (row index)
  - Numeric features integer‑scaled (e.g., multiply floats by 10) so encrypted avg works on integers.

### 2) Install Python deps (one-time)
```bash
cd jupyter-integration
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
(macOS: use `pip3` if `pip` is not found.)

### 3) Start the backend API (must be same shell where Blind Proxy works)
```bash
cd cube-server
node index.js
```
You should see it listening on `http://localhost:3001`. Keep this terminal open.

### 4) Start Jupyter Notebook
In a new terminal:
```bash
cd jupyter-integration
source venv/bin/activate
jupyter notebook Iris_Classification_Example.ipynb
# or without activating:
# ./venv/bin/jupyter notebook Iris_Classification_Example.ipynb
```
Open the URL printed in the terminal.

### 5) Configure notebook variables
In the notebook, set:
```python
ORGANIZATION = "blizzy-insizzy"
DATASET_SLUG = "iris"
SCHEMA_SLUG = "iris-3"
API_URL = "http://localhost:3001"
```

### 6) Run cells
- For encrypted workflows: run the encrypted aggregation sections.
- Plaintext section is illustrative only (not privacy-preserving).

## How to use (encrypted workflows)

1) Per-class means (integer-scaled):
   - In notebook section “Encrypted averages: sepal width per class”
   - Uses `avg(0~1000)` with `species:<class>` filter; returns mean per class without decrypting rows.

2) Batch means (all features):
   - Section “Encrypted averages per batch of 10 rows”
   - Uses `dataset-order` ranges (0~9, 10~19, …) plus `avg(0~1000)` per feature.

3) Encrypted classifier (integer counts):
   - Section “Encrypted Aggregation Classifier (no decryption)”
   - Searches thresholds using encrypted `count(<t)` per class; picks best threshold; no row decryption.

Adjusting for your data:
- If you scaled floats by 10, keep ranges like `0~1000`. If you scaled differently, adjust the ranges and thresholds accordingly.
- Threshold grid can be narrowed to speed up (e.g., `range(0, 301, 30)`).

Plaintext workflow (illustrative):
- The notebook still has a plaintext load and scikit-learn example (decrypt=True). Use only for comparison; it is not encrypted.

## API Endpoint

The backend provides a new endpoint for querying data:

**POST** `/api/blind/query`

Request body:
```json
{
  "organization": "your-org-slug",
  "datasetSlug": "dataset-slug",
  "schemaSlug": "schema-slug",
  "limit": 1000,
  "offset": 0
}
```

Response:
```json
{
  "success": true,
  "count": 150,
  "records": [
    {"sepal_length": 5.1, "sepal_width": 3.5, ...},
    ...
  ],
  "organization": "your-org-slug",
  "dataset": "dataset-slug",
  "schema": "schema-slug"
}
```

## Example: Iris Classification

The `Iris_Classification_Example.ipynb` notebook demonstrates:

1. Loading the Iris dataset from Blind Insight
2. Preparing data for classification
3. Training a logistic regression model
4. Evaluating model accuracy

This replaces the standard scikit-learn example:
```python
# Instead of:
from sklearn import datasets
iris = datasets.load_iris()

# Use:
from blind_insight_client import load_iris_from_blind
X, y = load_iris_from_blind(organization, dataset_slug, schema_slug)
```

## Files

- `blind_insight_client.py` - Python client library for querying Blind Insight
- `Iris_Classification_Example.ipynb` - Example Jupyter notebook with ML workflow
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Troubleshooting

- Backend 500 with “seed phrase” error: start `node index.js` in the same shell where `./blind organization list` and `./blind keyring inspect` work.
- Connection refused: make sure backend is running on port 3001.
- Slow encrypted classifier: narrow the threshold grid (e.g., `range(0, 301, 30)`).
- Aggregation errors: ensure numeric features are integer-scaled and ranges (e.g., `0~1000`) cover your data.
- Dataset/schemas not found: double-check slugs and that data is uploaded.

## Next Steps

- Add support for filtering and querying specific fields
- Implement data caching for better performance
- Add support for streaming large datasets
- Create additional example notebooks for other ML use cases


