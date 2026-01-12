"""
Blind Insight Python Client for Jupyter Notebooks

This client allows data scientists to query data from Blind Insight
and use it in machine learning workflows with scikit-learn, pandas, etc.
"""

import json
import os

import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any

# Check for environment variable to disable SSL verification (for local development)
BLINDINSIGHT_NOVERIFY_SSL = os.getenv("BLINDINSIGHT_NOVERIFY_SSL", "").lower() in ("true", "1", "yes")


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

    def __init__(
        self,
        api_url: str = "http://localhost:3001",
        backend_api_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        """
        Initialize the Blind Insight client.

        Args:
            api_url: Base URL of the proxy API (default: http://localhost:3001)
            backend_api_url: Optional base URL of the backend API for metadata lookups.
                           If not provided, will try to derive from api_url.
                           Default: None (auto-detect from api_url)
            username: Optional username for Basic Auth when accessing backend API.
                     If not provided, metadata lookups may fail with 403 errors.
            password: Optional password for Basic Auth when accessing backend API.
                     If not provided, metadata lookups may fail with 403 errors.
            verify_ssl: Optional SSL certificate verification setting.
                       If None, uses BLINDINSIGHT_NOVERIFY_SSL environment variable.
                       If True, verifies SSL certificates.
                       If False, disables SSL verification (for local development).
        """
        self.api_url = api_url.rstrip("/")
        self.backend_api_url = backend_api_url.rstrip("/") if backend_api_url else None
        self.username = username
        self.password = password
        
        # Determine SSL verification setting
        if verify_ssl is None:
            self.verify_ssl = not BLINDINSIGHT_NOVERIFY_SSL
        else:
            self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        # Set up Basic Auth if credentials are provided
        if self.username and self.password:
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(self.username, self.password)
        elif self.username or self.password:
            # One is provided but not both - warn user
            import warnings
            warnings.warn(
                "Only one of username/password provided. Authentication may fail. "
                "Provide both username and password for Basic Auth.",
                UserWarning
            )

    def query(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[List[str]] = None,
        decrypt: bool = False,
        schema_id: Optional[str] = None,  # Optional: provide schema ID directly to skip lookup
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
            decrypt: If True, first fetch encrypted records, then decrypt them via /api/records/decrypt/
                    This is required to get plaintext field names from encrypted data.
            schema_id: Optional schema ID. If provided, skips lookup from slugs. Useful if you know the schema ID.

        Returns:
            Dictionary containing 'success', 'count', 'records', 'encrypted', etc.

        Raises:
            requests.RequestException: If the API request fails
        """
        # Step 0: Get schema ID
        # The proxy search endpoint requires a schema ID, not slugs.
        # If schema_id is provided directly, use it. Otherwise, try to get it from slugs via backend API.
        if not schema_id:
            # Check if we have authentication - required for metadata lookups
            if not (self.username and self.password):
                raise ValueError(
                    f"Schema ID lookup requires authentication, but username/password not provided. "
                    f"Either:\n"
                    f"1. Provide schema_id directly: query(..., schema_id='your-schema-id')\n"
                    f"2. Create BlindInsightClient with authentication: BlindInsightClient(..., username='...', password='...')"
                )
            # Determine backend API URL for metadata lookups
            # The proxy forwards unmatched routes to the backend API, so we can use the proxy URL
            # if backend_api_url is not explicitly provided
            if self.backend_api_url:
                backend_url = self.backend_api_url
            else:
                # Use the proxy URL - it will forward metadata requests to the backend API
                # This is better than trying to derive the backend URL which may be incorrect
                backend_url = self.api_url
            
            try:
                # Get organization by slug using backend API (or proxy which forwards to backend)
                org_url = f"{backend_url.rstrip('/')}/api/organizations/by-slug/{organization}/"
                print(f"Attempting to get organization ID from: {org_url}")
                org_response = self.session.get(org_url)
                
                # Check response status
                if org_response.status_code != 200:
                    response_text = org_response.text[:500] if org_response.text else "(empty response)"
                    raise ValueError(
                        f"Failed to get organization. "
                        f"Status: {org_response.status_code}, "
                        f"Response: {response_text}"
                    )
                
                # Check if response body is empty
                if not org_response.text or len(org_response.text.strip()) == 0:
                    raise ValueError(
                        f"Received empty response from {org_url}. "
                        f"Status: {org_response.status_code}, "
                        f"Headers: {dict(org_response.headers)}"
                    )
                
                # Check if response is actually JSON
                content_type = org_response.headers.get('content-type', '').lower()
                if 'application/json' not in content_type:
                    response_text = org_response.text[:500]  # First 500 chars
                    raise ValueError(
                        f"Expected JSON response but got {content_type}. "
                        f"Response preview: {response_text}"
                    )
                
                try:
                    org_data = org_response.json()
                except json.JSONDecodeError as e:
                    response_text = org_response.text[:500]
                    raise ValueError(
                        f"Failed to parse JSON response. "
                        f"Status: {org_response.status_code}, "
                        f"Content-Type: {content_type}, "
                        f"Response preview: {response_text}"
                    ) from e
                
                org_id = org_data.get("id") or (org_data.get("url", "").rstrip("/").split("/")[-1] if org_data.get("url") else None)
                
                if not org_id:
                    raise ValueError(f"Could not extract organization ID from response: {org_data}")
                
                # Get dataset by slug
                dataset_url = f"{backend_url.rstrip('/')}/api/organizations/{org_id}/datasets/{dataset_slug}/"
                print(f"Attempting to get dataset ID from: {dataset_url}")
                dataset_response = self.session.get(dataset_url)
                
                if dataset_response.status_code != 200:
                    response_text = dataset_response.text[:500] if dataset_response.text else "(empty response)"
                    raise ValueError(
                        f"Failed to get dataset. "
                        f"Status: {dataset_response.status_code}, "
                        f"Response: {response_text}"
                    )
                
                if not dataset_response.text or len(dataset_response.text.strip()) == 0:
                    raise ValueError(
                        f"Received empty response from {dataset_url}. "
                        f"Status: {dataset_response.status_code}"
                    )
                
                content_type = dataset_response.headers.get('content-type', '').lower()
                if 'application/json' not in content_type:
                    response_text = dataset_response.text[:500]
                    raise ValueError(
                        f"Expected JSON response but got {content_type}. "
                        f"Response preview: {response_text}"
                    )
                
                try:
                    dataset_data = dataset_response.json()
                except json.JSONDecodeError as e:
                    response_text = dataset_response.text[:500]
                    raise ValueError(
                        f"Failed to parse JSON response. "
                        f"Status: {dataset_response.status_code}, "
                        f"Content-Type: {content_type}, "
                        f"Response preview: {response_text}"
                    ) from e
                
                dataset_id = dataset_data.get("id") or (dataset_data.get("url", "").rstrip("/").split("/")[-1] if dataset_data.get("url") else None)
                
                if not dataset_id:
                    raise ValueError(f"Could not extract dataset ID from response: {dataset_data}")
                
                # Get schema by slug
                schema_lookup_url = f"{backend_url.rstrip('/')}/api/datasets/{dataset_id}/schema/{schema_slug}/"
                print(f"Attempting to get schema ID from: {schema_lookup_url}")
                schema_response = self.session.get(schema_lookup_url)
                
                if schema_response.status_code != 200:
                    response_text = schema_response.text[:500] if schema_response.text else "(empty response)"
                    raise ValueError(
                        f"Failed to get schema. "
                        f"Status: {schema_response.status_code}, "
                        f"Response: {response_text}"
                    )
                
                if not schema_response.text or len(schema_response.text.strip()) == 0:
                    raise ValueError(
                        f"Received empty response from {schema_lookup_url}. "
                        f"Status: {schema_response.status_code}"
                    )
                
                content_type = schema_response.headers.get('content-type', '').lower()
                if 'application/json' not in content_type:
                    response_text = schema_response.text[:500]
                    raise ValueError(
                        f"Expected JSON response but got {content_type}. "
                        f"Response preview: {response_text}"
                    )
                
                try:
                    schema_data = schema_response.json()
                except json.JSONDecodeError as e:
                    response_text = schema_response.text[:500]
                    raise ValueError(
                        f"Failed to parse JSON response. "
                        f"Status: {schema_response.status_code}, "
                        f"Content-Type: {content_type}, "
                        f"Response preview: {response_text}"
                    ) from e
                
                schema_id = schema_data.get("id") or (schema_data.get("url", "").rstrip("/").split("/")[-1] if schema_data.get("url") else None)
                
                if not schema_id:
                    raise ValueError(f"Could not extract schema ID from response: {schema_data}")
                    
            except requests.exceptions.SSLError as e:
                ssl_hint = ""
                if self.verify_ssl:
                    ssl_hint = (
                        f" SSL certificate verification failed. "
                        f"For local development, you can disable SSL verification by: "
                        f"1. Setting environment variable: export BLINDINSIGHT_NOVERIFY_SSL=True, or "
                        f"2. Passing verify_ssl=False to BlindInsightClient(..., verify_ssl=False)."
                    )
                raise ValueError(
                    f"SSL error when trying to get schema ID from backend API at {backend_url}.{ssl_hint} "
                    f"Alternative options: "
                    f"1. Provide schema_id directly in the query() call "
                    f"2. Extract schema_id from a record's schema URL if you have access to records"
                ) from e
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    auth_hint = ""
                    if not (self.username and self.password):
                        auth_hint = (
                            f" Authentication is required. "
                            f"Provide username and password when creating BlindInsightClient: "
                            f"BlindInsightClient(api_url=..., username='your-email', password='your-password')."
                        )
                    raise ValueError(
                        f"Authentication failed (403 Forbidden) when trying to get schema ID from backend API at {backend_url}.{auth_hint} "
                        f"Alternative options: "
                        f"1. Provide schema_id directly in the query() call "
                        f"2. Extract schema_id from a record's schema URL if you have access to records"
                    ) from e
                else:
                    raise ValueError(
                        f"Could not get schema ID from slugs via backend API at {backend_url}. "
                        f"HTTP {e.response.status_code}: {e.response.text}. "
                        f"You can provide the schema_id directly if you know it."
                    ) from e
            except Exception as e:
                raise ValueError(
                    f"Could not get schema ID from slugs. "
                    f"Tried backend API at: {backend_url}. "
                    f"Error: {str(e)}. "
                    f"Make sure the backend API is accessible. "
                    f"You can provide the schema_id directly if you know it."
                ) from e
        
        # Step 1: Query encrypted records using proxy search endpoint
        # The proxy endpoint expects: {"schema": "<schema_id>", "filters": [{"label": "...", "value": "..."}], "limit": N, "offset": N}
        search_url = f"{self.api_url.rstrip('/')}/api/records/search/"
        
        # Convert string filters to object format if needed
        # The proxy expects filters as [{"label": "...", "value": "..."}]
        # For aggregations, the value can be like "count(0~1000)" or "avg(40~45)"
        # For regular filters, the value is just the value to match
        search_filters = []
        if filters:
            for filter_str in filters:
                if isinstance(filter_str, str):
                    # Parse "field:value" or "field:operation(range)" format
                    if ":" in filter_str:
                        label, value = filter_str.split(":", 1)
                        # The value can be an aggregation expression like "count(0~1000)"
                        # or a regular value like "0" or "fraud"
                        # Pass it through as-is - the proxy will parse it
                        search_filters.append({"label": label, "value": value})
                    else:
                        raise ValueError(f"Invalid filter format: {filter_str}. Expected 'field:value' or 'field:operation(range)'")
                elif isinstance(filter_str, dict):
                    # Already in correct format
                    search_filters.append(filter_str)
                else:
                    raise ValueError(f"Invalid filter format: {filter_str}")
        
        payload = {
            "schema": schema_id,
            "filters": search_filters,
            "limit": limit,
            "offset": offset,
        }
        
        response = self.session.post(search_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        # The proxy search endpoint returns a list of records directly
        if isinstance(result, list):
            encrypted_records = result
        elif isinstance(result, dict):
            encrypted_records = result.get("results", result.get("records", []))
            if not isinstance(encrypted_records, list):
                encrypted_records = [encrypted_records] if encrypted_records else []
        else:
            encrypted_records = []
        
        # Step 2: If decrypt=True, send encrypted records to decrypt endpoint
        # The decrypt endpoint expects an array of records with encrypted data
        # and returns decrypted records with plaintext field names
        if decrypt and encrypted_records:
            decrypt_url = f"{self.api_url.rstrip('/')}/api/records/decrypt/"
            decrypt_response = self.session.post(decrypt_url, json=encrypted_records)
            decrypt_response.raise_for_status()
            decrypted_records = decrypt_response.json()
            # The decrypt endpoint returns a list of decrypted records
            if isinstance(decrypted_records, list):
                return {"success": True, "records": decrypted_records}
            else:
                # Handle unexpected response format
                return {"success": True, "records": [decrypted_records] if decrypted_records else []}
        else:
            # Return encrypted records (with hashed field names)
            return {"success": True, "records": encrypted_records}

    def aggregate(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        agg_filter: str,
        extra_filters: Optional[List[str]] = None,
        decrypt: bool = False,
        schema_id: Optional[str] = None,  # Optional: provide schema ID directly to skip lookup
    ) -> Dict[str, Any]:
        """
        Run an aggregation query on encrypted data.
        
        NOTE: This method uses the proxy search endpoint. The proxy processes aggregation expressions
        and converts them to the appropriate backend API format. If you get 422 errors, the aggregation
        expression format might not be supported, or the proxy might need additional configuration.

        Args:
            organization: Blind Insight organization slug
            dataset_slug: Dataset slug
            schema_slug: Schema slug
            agg_filter: Aggregation expression, e.g. "amount:avg(0~10000)" or "device_risk_score:count(<50)"
            extra_filters: Optional list of additional filters (e.g., ["is_fraud:0"])
            decrypt: Should remain False for encrypted aggregation; set True only if you explicitly need plaintext.
            schema_id: Optional schema ID. If provided, skips lookup from slugs.

        Returns:
            Dictionary containing aggregation result. The aggregation value is typically in records[0]["data"]["value"].
        """
        # Use the query method, which will format filters correctly for the proxy
        # The proxy's records.Search function should handle aggregation expressions
        filters = extra_filters or []
        filters = filters + [agg_filter]

        try:
            result = self.query(
                organization=organization,
                dataset_slug=dataset_slug,
                schema_slug=schema_slug,
                limit=1,
                offset=0,
                filters=filters,
                decrypt=decrypt,
                schema_id=schema_id,
            )
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # Provide helpful error message for aggregation issues
                error_text = e.response.text[:500] if e.response.text else "(no error details)"
                raise ValueError(
                    f"Aggregation query failed (422 Unprocessable Entity). "
                    f"This might mean:\n"
                    f"1. The aggregation expression format is not supported: {agg_filter}\n"
                    f"2. The proxy might not be configured to handle aggregations\n"
                    f"3. Field names might need to be hashed (the proxy should handle this)\n"
                    f"Response: {error_text}\n"
                    f"Try using the backend API directly for aggregations, or check the aggregation expression format."
                ) from e
            raise

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
        schema_id: Optional[str] = None,  # Optional: provide schema ID directly to skip lookup
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
        result = self.query(organization, dataset_slug, schema_slug, limit, offset, filters, decrypt, schema_id=schema_id)
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
    
    def get_schema_id(
        self,
        organization: str,
        dataset_slug: str,
        schema_slug: str,
        backend_api_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> str:
        """
        Get schema ID from organization, dataset, and schema slugs.
        
        This method queries the backend API (not proxy) to resolve slugs to IDs.
        Requires authentication to the backend API.
        
        Args:
            organization: Organization slug
            dataset_slug: Dataset slug
            schema_slug: Schema slug
            backend_api_url: Optional backend API URL. If not provided, tries to derive from self.api_url.
            username: Optional username for Basic Auth. If not provided, uses self.username.
            password: Optional password for Basic Auth. If not provided, uses self.password.
            
        Returns:
            Schema ID string
            
        Raises:
            ValueError: If schema ID cannot be resolved
            requests.RequestException: If API requests fail
        """
        # Determine backend API URL
        if backend_api_url:
            backend_url = backend_api_url.rstrip("/")
        elif self.backend_api_url:
            backend_url = self.backend_api_url
        elif "proxy." in self.api_url:
            backend_url = self.api_url.replace("proxy.", "")
            if ":3001" not in backend_url and ":8080" not in backend_url:
                if backend_url.startswith("https://"):
                    backend_url = backend_url.replace("blindinsight.io", "blindinsight.io:3001")
                else:
                    backend_url = backend_url.replace("blindinsight.io", "blindinsight.io:3001")
        else:
            backend_url = self.api_url
        
        # Create a session for this request (use provided credentials or instance credentials)
        auth_username = username or self.username
        auth_password = password or self.password
        session = requests.Session()
        session.verify = self.verify_ssl
        if auth_username and auth_password:
            from requests.auth import HTTPBasicAuth
            session.auth = HTTPBasicAuth(auth_username, auth_password)
        
        # Get organization by slug
        # If using proxy URL, it will forward to backend API
        org_url = f"{backend_url}/api/organizations/by-slug/{organization}/"
        print(f"Attempting to get organization ID from: {org_url}")
        org_response = session.get(org_url)
        org_response.raise_for_status()
        org_data = org_response.json()
        org_id = org_data.get("id") or (org_data.get("url", "").rstrip("/").split("/")[-1] if org_data.get("url") else None)
        
        if not org_id:
            raise ValueError(f"Could not extract organization ID from response: {org_data}")
        
        # Get dataset by slug
        dataset_url = f"{backend_url}/api/organizations/{org_id}/datasets/{dataset_slug}/"
        dataset_response = session.get(dataset_url)
        dataset_response.raise_for_status()
        dataset_data = dataset_response.json()
        dataset_id = dataset_data.get("id") or (dataset_data.get("url", "").rstrip("/").split("/")[-1] if dataset_data.get("url") else None)
        
        if not dataset_id:
            raise ValueError(f"Could not extract dataset ID from response: {dataset_data}")
        
        # Get schema by slug
        schema_url = f"{backend_url}/api/datasets/{dataset_id}/schema/{schema_slug}/"
        schema_response = session.get(schema_url)
        schema_response.raise_for_status()
        schema_data = schema_response.json()
        schema_id = schema_data.get("id") or (schema_data.get("url", "").rstrip("/").split("/")[-1] if schema_data.get("url") else None)
        
        if not schema_id:
            raise ValueError(f"Could not extract schema ID from response: {schema_data}")
        
        return schema_id


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
    schema_id: Optional[str] = None,  # Optional: provide schema ID directly to skip lookup
    username: Optional[str] = None,  # Optional: username for backend API authentication
    password: Optional[str] = None,  # Optional: password for backend API authentication
    verify_ssl: Optional[bool] = None,  # Optional: SSL verification (default: from BLINDINSIGHT_NOVERIFY_SSL env var)
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
    client = BlindInsightClient(api_url=api_url, username=username, password=password, verify_ssl=verify_ssl)
    df = client.load_data(organization, dataset_slug, schema_slug, limit=10000, filters=filters, decrypt=decrypt, schema_id=schema_id)

    if df.empty:
        raise ValueError("No data returned from Blind Insight")

    # Handle nested data structure if present (common in Blind Insight responses)
    # Records may come as: [{"data": {"field1": val1, "field2": val2}, "schema": "...", "id": "..."}]
    # We need to expand the "data" dict into separate columns
    if 'data' in df.columns:
        # Check if data column contains dictionaries
        if df['data'].dtype == object:
            # Check if it's actually a dict column by sampling
            sample_val = df['data'].iloc[0] if len(df) > 0 else None
            if isinstance(sample_val, dict):
                # Expand nested dictionaries into separate columns
                # Use json_normalize to flatten the nested dict structure
                data_dicts = df['data'].apply(lambda x: x if isinstance(x, dict) else {})
                df_expanded = pd.json_normalize(data_dicts)
                
                # Drop the original 'data' column and merge expanded columns
                # Also drop other metadata columns that aren't needed for ML
                metadata_cols = ['data', 'schema', 'url', 'id', 'owner', 'dataset-order', 'dataset_order']
                cols_to_drop = [col for col in metadata_cols if col in df.columns]
                df = pd.concat([df.drop(cols_to_drop, axis=1), df_expanded], axis=1)
                
                # Debug output to help diagnose column issues
                print(f"Expanded DataFrame columns after flattening 'data': {df.columns.tolist()}")

    # Expected fraud dataset columns:
    # Features: risk_level, year, month, day (numeric)
    # Target: fraud_type or is_active

    # Debug: Print available columns to help diagnose issues
    print(f"Available columns in DataFrame: {df.columns.tolist()}")
    
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
        raise ValueError(
            f"Could not identify feature columns in the dataset. "
            f"Available columns: {df.columns.tolist()}. "
            f"Please specify feature_cols explicitly."
        )
    
    # Even if feature_cols is provided, we need to match them to actual column names
    # (handles case differences, hyphen/underscore variations, etc.)
    # This is especially important for encrypted data that was decrypted

    # Auto-detect target column if not provided
    if target_col is None:
        for col in ["fraud_type", "is_active", "target", "class", "label"]:
            if col in df.columns:
                target_col = col
                break

    if target_col is None:
        raise ValueError("Could not identify target column (expected: fraud_type, is_active, target, class, or label)")

    # Extract features and target
    # First, verify all columns exist, and try to match with case-insensitive and hyphen/underscore variations
    available_cols = df.columns.tolist()
    available_cols_lower = [c.lower() for c in available_cols]
    
    # Try to find matching columns (handle case and hyphen/underscore variations)
    matched_feature_cols = []
    for col in feature_cols:
        col_lower = col.lower()
        # Try exact match first
        if col in available_cols:
            matched_feature_cols.append(col)
        # Try case-insensitive match
        elif col_lower in available_cols_lower:
            idx = available_cols_lower.index(col_lower)
            matched_feature_cols.append(available_cols[idx])
        # Try hyphen/underscore variations
        else:
            col_variants = [col.replace('_', '-'), col.replace('-', '_')]
            found = False
            for variant in col_variants:
                if variant in available_cols:
                    matched_feature_cols.append(variant)
                    found = True
                    break
                variant_lower = variant.lower()
                if variant_lower in available_cols_lower:
                    idx = available_cols_lower.index(variant_lower)
                    matched_feature_cols.append(available_cols[idx])
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"Column '{col}' not found. Available columns: {available_cols}. "
                    f"Tried variations: {col_variants}"
                )
    
    # Same for target column
    matched_target_col = target_col
    if target_col not in available_cols:
        target_lower = target_col.lower()
        if target_lower in available_cols_lower:
            idx = available_cols_lower.index(target_lower)
            matched_target_col = available_cols[idx]
        else:
            target_variants = [target_col.replace('_', '-'), target_col.replace('-', '_')]
            found = False
            for variant in target_variants:
                if variant in available_cols:
                    matched_target_col = variant
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"Target column '{target_col}' not found. Available columns: {available_cols}"
                )
    
    print(f"Using feature columns: {matched_feature_cols}")
    print(f"Using target column: {matched_target_col}")
    
    X = df[matched_feature_cols].values
    y = df[matched_target_col].values

    # Convert target to numeric if it's string
    if y.dtype == object:
        from sklearn.preprocessing import LabelEncoder

        le = LabelEncoder()
        y = le.fit_transform(y)

    return X, y
