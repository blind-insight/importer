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

### 4. Prepare Your Dataset

You need to upload your dataset to Blind Insight before using it in the notebooks. See the [Dataset Setup](#dataset-setup) section below for detailed instructions.

## Dataset Setup

### Financial Fraud Dataset for `fraud_analysis.ipynb`

The `fraud_analysis.ipynb` notebook requires a financial fraud dataset with the following schema:

**Required Fields:**
- `transaction_id` (string) - Unique transaction identifier
- `user_id` (string) - User identifier
- `amount` (number) - Transaction amount (will be scaled to cents, e.g., 63.99 → 6399)
- `hour` (integer) - Hour of day (0-23)
- `country` (string) - Country code (e.g., "US", "FR", "UK")
- `transaction_type` (string) - Type of transaction (e.g., "ATM", "Online", "POS", "QR")
- `merchant_category` (string) - Category (e.g., "Food", "Travel", "Electronics")
- `device_risk_score` (integer) - Device risk score (0-100)
- `ip_risk_score` (integer) - IP risk score (0-100)
- `is_fraud` (integer) - Binary label (0 = not fraud, 1 = fraud)

#### Option 1: Upload Using the Blind CLI (Recommended)

If you have a fraud dataset ready:

1. **Create the dataset in Blind Insight:**
   ```bash
   blind dataset create --organization demo --name FraudAnalysis
   ```

2. **Create the schema:**
   Create a JSON schema file (e.g., `fraud_schema.json`) with the following structure:
   ```json
   {
     "type": "object",
     "properties": {
       "transaction_id": {"type": "string"},
       "user_id": {"type": "string"},
       "amount": {"type": "number", "minimum": 0},
       "hour": {"type": "integer", "minimum": 0, "maximum": 23},
       "country": {"type": "string"},
       "transaction_type": {"type": "string"},
       "merchant_category": {"type": "string"},
       "device_risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
       "ip_risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
       "is_fraud": {"type": "integer", "enum": [0, 1]}
     }
   }
   ```
   
   Then create the schema:
   ```bash
   blind schema create --organization demo --dataset FraudAnalysis --name FraudAnalysis --file fraud_schema.json
   ```

3. **Upload the data:**
   Prepare your data as a JSON array of records:
   ```json
   [
     {
       "transaction_id": "txn_001",
       "user_id": "user_123",
       "amount": 63.99,
       "hour": 14,
       "country": "US",
       "transaction_type": "Online",
       "merchant_category": "Food",
       "device_risk_score": 25,
       "ip_risk_score": 30,
       "is_fraud": 0
     },
     ...
   ]
   ```
   
   Upload using:
   ```bash
   blind record create --organization demo --dataset FraudAnalysis --schema FraudAnalysis --file fraud_data.json
   ```

#### Option 2: Use Demo Datasets

Demo datasets are available in the `demo-datasets` directory at the project root:

1. **Navigate to demo-datasets:**
   ```bash
   cd ../demo-datasets
   ```

2. **Follow the demo-datasets README:**
   See [`../demo-datasets/README.md`](../demo-datasets/README.md) for instructions on:
   - Available datasets
   - How to create datasets using the `blind` CLI
   - How to generate synthetic data using the `generate` script

3. **Download pre-built datasets:**
   Check the [demo-datasets releases](https://github.com/blind-insight/demo-datasets/releases) for pre-built dataset files.

#### Option 3: Use the Importer Tool (BigQuery/Other Sources)

If your fraud data is in BigQuery or another data source:

1. **Navigate to the importer directory:**
   ```bash
   cd ..
   ```

2. **Follow the importer README:**
   See [`../README.md`](../README.md) for instructions on:
   - Extracting schemas from BigQuery
   - Converting schemas to JSON Schema format
   - Importing data into Blind Insight

3. **Use the web UI:**
   - Start the backend: `cd cube-server && node index.js`
   - Start the frontend: `python3 -m http.server 3000`
   - Open http://localhost:3000
   - Follow the UI to import your BigQuery table

#### Option 4: Create Synthetic Fraud Data

You can create synthetic fraud data for testing:

1. **Generate data using Python:**
   ```python
   import json
   import random
   from faker import Faker
   
   fake = Faker()
   
   countries = ["US", "UK", "FR", "DE", "TR", "NG"]
   transaction_types = ["ATM", "Online", "POS", "QR"]
   merchant_categories = ["Food", "Travel", "Electronics", "Clothing", "Grocery"]
   
   records = []
   for i in range(10000):
       is_fraud = random.choices([0, 1], weights=[95, 5])[0]  # ~5% fraud rate
       records.append({
           "transaction_id": f"txn_{i:06d}",
           "user_id": f"user_{random.randint(1, 1000):04d}",
           "amount": round(random.uniform(10, 5000), 2),
           "hour": random.randint(0, 23),
           "country": random.choice(countries),
           "transaction_type": random.choice(transaction_types),
           "merchant_category": random.choice(merchant_categories),
           "device_risk_score": random.randint(0, 100),
           "ip_risk_score": random.randint(0, 100),
           "is_fraud": is_fraud
       })
   
   with open("fraud_data.json", "w") as f:
       json.dump(records, f, indent=2)
   ```

2. **Upload the generated data:**
   ```bash
   blind record create --organization demo --dataset FraudAnalysis --schema FraudAnalysis --file fraud_data.json
   ```

### Verify Dataset Configuration

After uploading, verify your dataset is accessible:

```bash
# List datasets
blind dataset list --organization demo

# List schemas in a dataset
blind schema list --organization demo --dataset FraudAnalysis

# Check record count (if supported)
# You can verify in the Blind Insight UI or by querying through the notebook
```

### Update Notebook Configuration

Once your dataset is uploaded, update the configuration in `fraud_analysis.ipynb`:

```python
ORGANIZATION = "demo"  # Your organization slug
DATASET_SLUG = "FraudAnalysis"  # Your dataset slug
SCHEMA_SLUG = "FraudAnalysis"  # Your schema slug
SCHEMA_ID = "your-schema-id"  # Optional: Get from schema details if needed
```

### Further Reading

- **Blind Insight Documentation:** [Getting Started Guide](https://docs.blindinsight.io/getting-started/)
- **Blind Proxy CLI:** [CLI Documentation](https://docs.blindinsight.io/)
- **Demo Datasets:** See [`../demo-datasets/README.md`](../demo-datasets/README.md)
- **Importer Tool:** See [`../README.md`](../README.md)

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
- `Iris_Classification_Example.ipynb` - Example Jupyter notebook with Iris classification
- `fraud_analysis.ipynb` - Financial fraud detection notebook (see [Dataset Setup](#dataset-setup) for dataset requirements)
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


