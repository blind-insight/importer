# Encrypted Search with Blind Insight

## Overview

Blind Insight is a **searchable encryption** product that allows you to query and analyze **encrypted data** without decrypting it first. This is a key security feature that maintains data privacy even during analysis.

## How It Works

### Encrypted Search (Default)

By default, queries to Blind Insight **do NOT decrypt** the data. Instead, they use encrypted search capabilities:

- **Equality queries**: `"field:value"` - Find records where field equals value (encrypted)
- **Comparisons**: `"field:>40"`, `"field:<17"`, `"field:>=47"`, `"field:<=17"`
- **Ranges**: `"field:40~45"` - Find records in range (encrypted)
- **Aggregations**: 
  - `"field:avg(40~45)"` - Average on encrypted data
  - `"field:sum(>40)"` - Sum on encrypted data
  - `"field:count(<15)"` - Count on encrypted data
  - `"field:min(>=35)"` - Minimum on encrypted data
  - `"field:max(<45)"` - Maximum on encrypted data

### When Decryption is Needed

Decryption is **only required** for operations that need plaintext data:
- Machine Learning (scikit-learn, numpy, pandas need plaintext)
- Displaying data to users
- Exporting data

**Important**: Even when decryption is needed, you can:
1. Use encrypted filters to narrow down the dataset
2. Only decrypt the filtered results
3. Minimize the amount of data that needs decryption

## Usage Examples

### Encrypted Query (No Decryption)

```python
from blind_insight_client import BlindInsightClient

client = BlindInsightClient()

# Query encrypted data - NO decryption
result = client.query(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    limit=100,
    decrypt=False  # Data stays encrypted
)

# Result contains encrypted records
print(f"Encrypted: {result['encrypted']}")  # True
```

### Encrypted Search with Filters

```python
# Search encrypted data using filters
result = client.query(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    filters=["sepal-length:>5.0", "petal-width:<1.5"],  # Encrypted filters
    decrypt=False  # Still encrypted
)

# Only matching records returned (still encrypted)
print(f"Found {result['count']} matching records (encrypted)")
```

### Encrypted Aggregations

```python
# Calculate average on encrypted data
result = client.query(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    filters=["sepal-length:avg(4.0~6.0)"],  # Average on encrypted range
    decrypt=False
)

# Result contains aggregation value (calculated on encrypted data)
print(f"Average: {result['records'][0]['data']['value']}")
```

### Decryption for ML (When Needed)

```python
from blind_insight_client import load_iris_from_blind

# For ML, we need plaintext - but we can filter first
X, y = load_iris_from_blind(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    filters=["sepal-length:>5.0"],  # Filter encrypted data first
    decrypt=True  # Then decrypt only filtered results
)

# Now use with scikit-learn
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression()
clf.fit(X, y)
```

## Security Model

1. **Data at Rest**: Always encrypted in Blind Insight
2. **Encrypted Queries**: Search, filter, aggregate without decryption
3. **Selective Decryption**: Only decrypt when absolutely necessary
4. **Minimal Exposure**: Use filters to minimize decrypted data

## Supported Query Types

Based on [Blind Insight documentation](https://docs.blindinsight.io/getting-started/using-the-blind-proxy/#supported-query-types):

### Strings
- Equality: `"name:John"`
- Partial match: `"name:John*"` (if supported)

### Numbers
- Equality: `"age:47"`
- Greater than: `"age:>40"`
- Less than: `"age:<17"`
- Greater or equal: `"age:>=47"`
- Less or equal: `"age:<=17"`
- Range: `"age:40~45"`

### Aggregations (on encrypted data)
- Average: `"age:avg(40~45)"`
- Sum: `"age:sum(>40)"`
- Count: `"age:count(<15)"`
- Min: `"age:min(>=35)"`
- Max: `"age:max(<45)"`

## Best Practices

1. **Use encrypted filters first**: Narrow down dataset before decryption
2. **Only decrypt when needed**: ML operations require plaintext, but filter first
3. **Use aggregations**: Calculate statistics on encrypted data when possible
4. **Minimize decrypted data**: Only decrypt the records you actually need

## Example: Efficient ML Workflow

```python
# Step 1: Use encrypted aggregation to understand data
client = BlindInsightClient()
stats = client.query(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    filters=["sepal-length:avg(0~10)"],  # Average on encrypted data
    decrypt=False
)
print(f"Average sepal length: {stats['records'][0]['data']['value']}")

# Step 2: Filter encrypted data to relevant subset
# Step 3: Only decrypt the filtered subset for ML
X, y = load_iris_from_blind(
    organization="blizzy-insizzy",
    dataset_slug="iris",
    schema_slug="iris-3",
    filters=["sepal-length:>5.0"],  # Encrypted filter
    decrypt=True  # Decrypt only filtered results
)

# Step 4: Train model on minimal decrypted data
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression()
clf.fit(X, y)
```

## References

- [Blind Insight Documentation](https://docs.blindinsight.io)
- [Supported Query Types](https://docs.blindinsight.io/getting-started/using-the-blind-proxy/#supported-query-types)
- [API Reference](https://docs.blindinsight.io/api-reference/)

