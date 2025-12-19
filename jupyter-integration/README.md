# Jupyter Notebook Integration with Blind Insight

This directory contains the integration components that allow data scientists to use Blind Insight data in Jupyter Notebooks for machine learning workflows.

## Overview

This integration enables data scientists to:
- Query encrypted data from Blind Insight
- Use the data with standard ML libraries (scikit-learn, pandas, numpy)
- Work seamlessly in Jupyter Notebooks
- Maintain privacy and security while doing data science

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

### 1. Install Python Dependencies

**Option A: Using a Virtual Environment (Recommended)**

```bash
cd jupyter-integration
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option B: Install System-Wide (macOS)**

```bash
cd jupyter-integration
pip3 install -r requirements.txt
```

**Note**: On macOS, you may need to use `pip3` instead of `pip`. If you get "command not found", try `pip3`.

### 2. Start the Backend API

The backend API must be running to serve queries. From the project root:

```bash
cd cube-server
node index.js
```

The API will run on `http://localhost:3001` by default.

### 3. Verify Blind Proxy Authentication

Make sure you're authenticated with Blind Insight:

```bash
../blind/blind login
../blind/blind organization list
```

### 4. Upload Your Data to Blind Insight

Use the main importer tool to upload your dataset (e.g., Iris dataset) to Blind Insight. Note the:
- Organization slug
- Dataset slug
- Schema slug

You'll need these values in your notebook.

## Usage

### Quick Start

1. Open the example notebook:
   ```bash
   # From the repo root:
   cd jupyter-integration
   # Option A (activate venv):
   source venv/bin/activate
   jupyter notebook Iris_Classification_Example.ipynb
   # Option B (without activating venv):
   ./venv/bin/jupyter notebook Iris_Classification_Example.ipynb
   ```

2. Update the configuration in the notebook:
   ```python
   ORGANIZATION = "your-organization-slug"
   DATASET_SLUG = "iris-dataset"
   SCHEMA_SLUG = "iris-schema"
   ```

3. Run the cells to load data and train your model!

### Using the Client in Your Own Notebooks

```python
from blind_insight_client import BlindInsightClient, load_iris_from_blind

# Option 1: Load data in scikit-learn format (X, y)
X, y = load_iris_from_blind(
    organization="my-org",
    dataset_slug="iris-dataset",
    schema_slug="iris-schema"
)

# Option 2: Load as pandas DataFrame
client = BlindInsightClient(api_url="http://localhost:3001")
df = client.load_data(
    organization="my-org",
    dataset_slug="iris-dataset",
    schema_slug="iris-schema",
    limit=1000
)
```

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

### "Connection refused" error

- Ensure the backend API is running on port 3001
- Check that the API_URL in your notebook matches the backend URL

### "Authentication failed" error

- Run `../blind/blind login` to authenticate
- Verify with `../blind/blind organization list`

### "Dataset/Schema not found" error

- Verify the organization, dataset, and schema slugs are correct
- Ensure the data was successfully imported to Blind Insight

### "No data returned" error

- Check that records exist in the Blind Insight schema
- Verify the limit parameter isn't too restrictive
- Check backend logs for detailed error messages

## Next Steps

- Add support for filtering and querying specific fields
- Implement data caching for better performance
- Add support for streaming large datasets
- Create additional example notebooks for other ML use cases


