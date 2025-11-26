"""
Blind Insight Python Client for Jupyter Notebooks

This client allows data scientists to query data from Blind Insight
and use it in machine learning workflows with scikit-learn, pandas, etc.
"""

import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any


class BlindInsightClient:
    """
    Client for querying data from Blind Insight via the backend API.
    
    Example:
        >>> client = BlindInsightClient(api_url="http://localhost:3001")
        >>> data = client.query(
        ...     organization="my-org",
        ...     dataset_slug="iris-dataset",
        ...     schema_slug="iris-schema",
        ...     limit=150
        ... )
        >>> df = client.to_dataframe(data)
        >>> X = df[['sepal_length', 'sepal_width', 'petal_length', 'petal_width']].values
        >>> y = df['species'].values
    """
    
    def __init__(self, api_url: str = "http://localhost:3001"):
        """
        Initialize the Blind Insight client.
        
        Args:
            api_url: Base URL of the backend API (default: http://localhost:3001)
        """
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
    
    def query(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[List[str]] = None,
        decrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Query records from Blind Insight using encrypted search.
        
        Blind Insight supports encrypted queries without decryption:
        - Equality: "field:value"
        - Comparisons: "field:>40", "field:<17", "field:>=47", "field:<=17"
        - Ranges: "field:40~45"
        - Aggregations: "field:avg(40~45)", "field:sum(>40)", "field:count(<15)", etc.
        
        Args:
            organization: Blind Insight organization slug
            dataset_slug: Dataset slug in Blind Insight
            schema_slug: Schema slug in Blind Insight
            limit: Maximum number of records to return (default: 1000)
            offset: Number of records to skip (default: 0)
            filters: List of encrypted filter strings (e.g., ["age:>40", "name:John"])
            decrypt: If True, decrypt data (only needed for ML operations that require plaintext)
        
        Returns:
            Dictionary containing 'success', 'count', 'records', 'encrypted', etc.
        
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.api_url}/api/blind/query"
        
        payload = {
            "organization": organization,
            "datasetSlug": dataset_slug,
            "schemaSlug": schema_slug,
            "limit": limit,
            "offset": offset,
            "filters": filters or [],
            "decrypt": decrypt
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def to_dataframe(
        self,
        query_result: Dict[str, Any],
        records_key: str = "records"
    ) -> pd.DataFrame:
        """
        Convert query result to a pandas DataFrame.
        
        Args:
            query_result: Result dictionary from query() method
            records_key: Key in the result dictionary containing records (default: "records")
        
        Returns:
            pandas DataFrame with the records
        """
        if not query_result.get("success"):
            raise ValueError(f"Query was not successful: {query_result.get('error', 'Unknown error')}")
        
        records = query_result.get(records_key, [])
        
        if not records:
            # Return empty DataFrame with proper structure if no records
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        return df
    
    def load_data(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[List[str]] = None,
        decrypt: bool = True  # Default to True for DataFrame conversion (needs plaintext)
    ) -> pd.DataFrame:
        """
        Convenience method to query and convert to DataFrame in one step.
        
        Note: This method defaults to decrypt=True because pandas DataFrames require plaintext data.
        For encrypted queries without decryption, use query() directly.
        
        Args:
            organization: Blind Insight organization slug
            dataset_slug: Dataset slug in Blind Insight
            schema_slug: Schema slug in Blind Insight
            limit: Maximum number of records to return (default: 1000)
            offset: Number of records to skip (default: 0)
            filters: List of encrypted filter strings for encrypted search
            decrypt: If True, decrypt data (default: True for DataFrame conversion)
        
        Returns:
            pandas DataFrame with the queried records
        """
        result = self.query(organization, dataset_slug, schema_slug, limit, offset, filters, decrypt)
        return self.to_dataframe(result)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is available and healthy.
        
        Returns:
            Dictionary with API status
        """
        url = f"{self.api_url}/api/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


def load_iris_from_blind(
    organization: str,
    dataset_slug: str,
    schema_slug: str,
    api_url: str = "http://localhost:3001",
    filters: Optional[List[str]] = None,
    decrypt: bool = True  # Must be True for ML - scikit-learn needs plaintext
) -> tuple:
    """
    Load Iris dataset from Blind Insight in a format compatible with scikit-learn.
    
    This function mimics sklearn.datasets.load_iris() but loads data from Blind Insight.
    
    Note: This function requires decrypt=True because scikit-learn needs plaintext data.
    However, you can use encrypted filters to narrow down the dataset before decryption.
    
    Args:
        organization: Blind Insight organization slug
        dataset_slug: Dataset slug containing the Iris data
        schema_slug: Schema slug containing the Iris data
        api_url: Base URL of the backend API (default: http://localhost:3001)
        filters: Optional list of encrypted filter strings (e.g., ["sepal-length:>5.0"])
        decrypt: Must be True for ML use (scikit-learn requires plaintext) - default: True
    
    Returns:
        Tuple of (X, y) where:
        - X: numpy array of shape (n_samples, n_features) with feature data
        - y: numpy array of shape (n_samples,) with target labels
    
    Example:
        >>> # Load all data (decrypted for ML)
        >>> X, y = load_iris_from_blind(
        ...     organization="my-org",
        ...     dataset_slug="iris-dataset",
        ...     schema_slug="iris-schema"
        ... )
        >>> 
        >>> # Or use encrypted filters first, then decrypt only filtered results
        >>> X, y = load_iris_from_blind(
        ...     organization="my-org",
        ...     dataset_slug="iris-dataset",
        ...     schema_slug="iris-schema",
        ...     filters=["sepal-length:>5.0"]  # Encrypted filter
        ... )
        >>> # Use X and y with scikit-learn
        >>> from sklearn.linear_model import LogisticRegression
        >>> clf = LogisticRegression()
        >>> clf.fit(X, y)
    """
    client = BlindInsightClient(api_url=api_url)
    df = client.load_data(organization, dataset_slug, schema_slug, limit=150, filters=filters, decrypt=decrypt)
    
    if df.empty:
        raise ValueError("No data returned from Blind Insight")
    
    # Expected Iris dataset columns:
    # - sepal_length, sepal_width, petal_length, petal_width (features) - with underscore or hyphen
    # - species or target (label)
    
    # Try to find feature columns (handle both underscore and hyphen formats)
    feature_cols = []
    # Try underscore format first
    for col in ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']:
        if col in df.columns:
            feature_cols.append(col)
    
    # If not found, try hyphen format
    if not feature_cols:
        for col in ['sepal-length', 'sepal-width', 'petal-length', 'petal-width']:
            if col in df.columns:
                feature_cols.append(col)
    
    if not feature_cols:
        # If standard names not found, use all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        target_cols = ['species', 'target', 'class', 'label', 'dataset-order', 'dataset_order']
        feature_cols = [col for col in numeric_cols if col.lower() not in [t.lower() for t in target_cols]]
    
    if not feature_cols:
        raise ValueError("Could not identify feature columns in the dataset")
    
    # Try to find target column
    target_col = None
    for col in ['species', 'target', 'class', 'label']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column (expected: species, target, class, or label)")
    
    # Extract features and target
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Convert target to numeric if it's string
    if y.dtype == object:
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y = le.fit_transform(y)
    
    return X, y


