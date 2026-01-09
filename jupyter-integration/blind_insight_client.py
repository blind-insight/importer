"""
Blind Insight Python Client for Jupyter Notebooks

This client allows data scientists to query data from Blind Insight
and use it in machine learning workflows with scikit-learn, pandas, etc.
"""

import json

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
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session()

    def query(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[List[str]] = None,
        decrypt: bool = False,
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
        url = f"{self.api_url}/api/records/search"

        payload = {
            "organization": organization,
            "datasetSlug": dataset_slug,
            "schemaSlug": schema_slug,
            "limit": limit,
            "offset": offset,
            "filters": filters or [],
            "decrypt": decrypt,
        }
        payload = {"schema": "oKVxDa56fi4EwrgjpNiibw", "filters": [], "limit": 25, "offset": 0}

        response = self.session.post(
            url="https://proxy.local.blindinsight.io/api/records/search/",
            headers={
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Cookie": "_ga=GA1.1.556328847.1762024733; intercom-id-gldix7ww=3845f7c3-a2f0-42df-b6ba-afa92badfc0a; intercom-device-id-gldix7ww=3f61e658-dcfb-42fa-b22b-3bca06655440; fpestid=rPfSAHMfz6nSlB3qsGPb-wGIG7lzx5CoYXEMGJ6twDqa9rvNlRHpcQmRu8BfrrgLiOPGBA; _cc_id=7777fa457942de128b91c84cd6b2d18f; csrftoken=ELhrxIAixEGptaggw0LlYqn64iHrMoLm; _gcl_au=1.1.797926855.1762024733.1818048911.1766520779.1766520781; csrftoken=FrPZB8yTKcFADcGiGPsPSO20u5KbcYob; sessionid=g7lduckik4roej4uqx3876qak9by9s0e; intercom-session-gldix7ww=YW93MDhyNXlRK2xPWlZRTEVVSktxNExXTHBTeWNHc3BnYldhcEJ4UTRSdGppck12akV4c1dXRWJPNWxZSFFZUGJWZFhKa1BkMFJXT0hUdVlrMHJrMXZCTXF3a3l5Tk0vV0tNbGxBZG83VGs9LS0vajdYcHlKcTZGODlQcGpVTzZVYlJnPT0=--a7a7029b2df210376ba5200ff33b700eba391da8; _ga_1R54M8PY09=GS2.1.s1767921664$o64$g1$t1767923739$j60$l0$h205566794",
                "Origin": "https://local.blindinsight.io:3001",
                "Priority": "u=1, i",
                "Referer": "https://local.blindinsight.io:3001/",
                "Sec-Ch-Ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                "X-Csrftoken": "FrPZB8yTKcFADcGiGPsPSO20u5KbcYob",
            },
            data=json.dumps({"filters": [], "offset": 0, "schema": "oKVxDa56fi4EwrgjpNiibw", "limit": 25}),
        )

        # response = self.session.post(url, json=payload)
        response.raise_for_status()

        return {"success": bool(response.status_code == 200), "records": response.json()}

    def aggregate(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        agg_filter: str,
        extra_filters: Optional[List[str]] = None,
        decrypt: bool = False,
    ) -> Dict[str, Any]:
        """
        Run an aggregation query on encrypted data.

        Args:
            organization: Blind Insight organization slug
            dataset_slug: Dataset slug
            schema_slug: Schema slug
            agg_filter: Aggregation expression, e.g. "sepal-length:avg(0~10)" or "petal-width:count(<1.0)"
            extra_filters: Optional list of additional filters (e.g., ["species:I. setosa"])
            decrypt: Should remain False for encrypted aggregation; set True only if you explicitly need plaintext.

        Returns:
            Dictionary containing aggregation result. The aggregation value is typically in records[0]["data"]["value"].
        """
        filters = extra_filters or []
        filters = filters + [agg_filter]

        result = self.query(
            organization=organization,
            dataset_slug=dataset_slug,
            schema_slug=schema_slug,
            limit=1,
            offset=0,
            filters=filters,
            decrypt=decrypt,
        )
        return result

    def to_dataframe(self, query_result: Dict[str, Any], records_key: str = "records") -> pd.DataFrame:
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
        decrypt: bool = True,  # Default to True for DataFrame conversion (needs plaintext)
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
        url = f"{self.api_url}/api/status/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


def load_iris_from_blind(
    organization: str,
    dataset_slug: str,
    schema_slug: str,
    api_url: str = "http://localhost:3001",
    filters: Optional[List[str]] = None,
    decrypt: bool = True,  # Must be True for ML - scikit-learn needs plaintext
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

    # Try to find feature columns (handle both underscore and hyphen formats, union them)
    feature_cols = []
    underscore_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    hyphen_cols = ["sepal-length", "sepal-width", "petal-length", "petal-width"]

    for col in underscore_cols:
        if col in df.columns and col not in feature_cols:
            feature_cols.append(col)
    for col in hyphen_cols:
        if col in df.columns and col not in feature_cols:
            feature_cols.append(col)

    if not feature_cols:
        # If standard names not found, use all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        target_cols = ["species", "target", "class", "label", "dataset-order", "dataset_order"]
        feature_cols = [col for col in numeric_cols if col.lower() not in [t.lower() for t in target_cols]]

    if not feature_cols:
        raise ValueError("Could not identify feature columns in the dataset")

    # Try to find target column
    target_col = None
    for col in ["species", "target", "class", "label"]:
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


def load_fraud_from_blind(
    organization: str,
    dataset_slug: str,
    schema_slug: str,
    api_url: str = "http://localhost:3001",
    filters: Optional[List[str]] = None,
    decrypt: bool = True,  # Must be True for ML - scikit-learn needs plaintext
    feature_cols: Optional[List[str]] = None,
    target_col: Optional[str] = None,
) -> tuple:
    """
    Load financial fraud dataset from Blind Insight in a format compatible with scikit-learn.

    This function loads fraud detection data from Blind Insight and prepares it for ML.

    Note: This function requires decrypt=True because scikit-learn needs plaintext data.
    However, you can use encrypted filters to narrow down the dataset before decryption.

    Args:
        organization: Blind Insight organization slug
        dataset_slug: Dataset slug containing the fraud data
        schema_slug: Schema slug containing the fraud data
        api_url: Base URL of the backend API (default: http://localhost:3001)
        filters: Optional list of encrypted filter strings (e.g., ["risk-level:>50"])
        decrypt: Must be True for ML use (scikit-learn requires plaintext) - default: True
        feature_cols: Optional list of feature column names. If None, auto-detects numeric features.
        target_col: Optional target column name. If None, uses 'fraud_type' or 'is_active'.

    Returns:
        Tuple of (X, y) where:
        - X: numpy array of shape (n_samples, n_features) with feature data
        - y: numpy array of shape (n_samples,) with target labels

    Example:
        >>> # Load all data (decrypted for ML)
        >>> X, y = load_fraud_from_blind(
        ...     organization="demo",
        ...     dataset_slug="financial",
        ...     schema_slug="antifraud"
        ... )
        >>>
        >>> # Or use encrypted filters first, then decrypt only filtered results
        >>> X, y = load_fraud_from_blind(
        ...     organization="demo",
        ...     dataset_slug="financial",
        ...     schema_slug="antifraud",
        ...     filters=["risk-level:>50"]  # Encrypted filter
        ... )
        >>> # Use X and y with scikit-learn
        >>> from sklearn.linear_model import LogisticRegression
        >>> clf = LogisticRegression()
        >>> clf.fit(X, y)
    """
    client = BlindInsightClient(api_url=api_url)
    df = client.load_data(organization, dataset_slug, schema_slug, limit=10000, filters=filters, decrypt=decrypt)

    if df.empty:
        raise ValueError("No data returned from Blind Insight")

    # Handle nested data structure if present (common in Blind Insight responses)
    # Records may come as: [{"data": {"field1": val1, "field2": val2}}]
    if 'data' in df.columns:
        # If data is a dict column, expand it
        if df['data'].dtype == object:
            # Check if it's actually a dict column
            sample_val = df['data'].iloc[0] if len(df) > 0 else None
            if isinstance(sample_val, dict):
                # Expand nested dictionaries into separate columns
                data_dict = df['data'].apply(lambda x: x if isinstance(x, dict) else {})
                df_expanded = pd.json_normalize(data_dict)
                # Drop the original 'data' column and merge expanded columns
                df = pd.concat([df.drop('data', axis=1), df_expanded], axis=1)

    # Expected fraud dataset columns:
    # Features: risk_level, year, month, day (numeric)
    # Target: fraud_type or is_active

    # Auto-detect feature columns if not provided
    if feature_cols is None:
        # Try common fraud feature names (handle both underscore and hyphen)
        potential_features = [
            "risk_level", "risk-level",
            "year", "month", "day"
        ]
        feature_cols = []
        for col in potential_features:
            if col in df.columns and col not in feature_cols:
                feature_cols.append(col)
        
        # If no standard names found, use all numeric columns except target
        if not feature_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            target_cols = ["fraud_type", "is_active", "target", "class", "label", 
                          "report_id", "reporting_bank_id", "dataset-order", "dataset_order"]
            feature_cols = [col for col in numeric_cols if col.lower() not in [t.lower() for t in target_cols]]

    if not feature_cols:
        raise ValueError("Could not identify feature columns in the dataset")

    # Auto-detect target column if not provided
    if target_col is None:
        for col in ["fraud_type", "is_active", "target", "class", "label"]:
            if col in df.columns:
                target_col = col
                break

    if target_col is None:
        raise ValueError("Could not identify target column (expected: fraud_type, is_active, target, class, or label)")

    # Extract features and target
    X = df[feature_cols].values
    y = df[target_col].values

    # Convert target to numeric if it's string
    if y.dtype == object:
        from sklearn.preprocessing import LabelEncoder

        le = LabelEncoder()
        y = le.fit_transform(y)

    return X, y
