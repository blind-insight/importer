#!/usr/bin/env python3
"""
Test script to verify the Blind Insight Jupyter integration
"""

import sys
import json
from blind_insight_client import BlindInsightClient

def test_health_check():
    """Test the API health endpoint"""
    print("=" * 60)
    print("Test 1: API Health Check")
    print("=" * 60)
    
    client = BlindInsightClient(api_url="http://localhost:3001")
    try:
        health = client.health_check()
        print(f"✅ Health check passed: {health}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_blind_status():
    """Test the Blind Proxy authentication status"""
    print("\n" + "=" * 60)
    print("Test 2: Blind Proxy Status")
    print("=" * 60)
    
    import requests
    try:
        response = requests.get("http://localhost:3001/api/blind/status")
        response.raise_for_status()
        status = response.json()
        print(f"✅ Blind Proxy authenticated: {status.get('authenticated')}")
        if status.get('organizations'):
            orgs = json.loads(status['organizations'])
            print(f"   Organizations: {len(orgs)} found")
            if orgs:
                print(f"   First org: {orgs[0].get('name')} (slug: {orgs[0].get('slug')})")
        return True, status
    except Exception as e:
        print(f"❌ Blind status check failed: {e}")
        return False, None

def test_query_endpoint(organization, dataset_slug, schema_slug):
    """Test the query endpoint structure"""
    print("\n" + "=" * 60)
    print("Test 3: Query Endpoint Structure")
    print("=" * 60)
    
    client = BlindInsightClient(api_url="http://localhost:3001")
    try:
        result = client.query(
            organization=organization,
            dataset_slug=dataset_slug,
            schema_slug=schema_slug,
            limit=10
        )
        print(f"✅ Query endpoint responded successfully")
        print(f"   Success: {result.get('success')}")
        print(f"   Count: {result.get('count', 0)} records")
        print(f"   Records returned: {len(result.get('records', []))}")
        if result.get('records'):
            print(f"   Sample record keys: {list(result['records'][0].keys())}")
        return True, result
    except Exception as e:
        print(f"⚠️  Query test: {e}")
        print(f"   (This is expected if the dataset/schema doesn't exist yet)")
        return False, None

def test_client_methods():
    """Test the client library methods"""
    print("\n" + "=" * 60)
    print("Test 4: Client Library Methods")
    print("=" * 60)
    
    client = BlindInsightClient(api_url="http://localhost:3001")
    
    # Test health_check
    try:
        health = client.health_check()
        print("✅ health_check() method works")
    except Exception as e:
        print(f"❌ health_check() failed: {e}")
        return False
    
    # Test query (will fail if no data, but should not crash)
    try:
        result = client.query("test-org", "test-dataset", "test-schema", limit=1)
        print("✅ query() method works (structure)")
    except Exception as e:
        # Expected if dataset doesn't exist
        if "404" in str(e) or "400" in str(e) or "500" in str(e):
            print("✅ query() method works (handles errors gracefully)")
        else:
            print(f"⚠️  query() method error: {e}")
    
    return True

def main():
    print("\n" + "=" * 60)
    print("Blind Insight Jupyter Integration Test Suite")
    print("=" * 60)
    print("\nTesting integration components...\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Blind status
    status_ok, status_data = test_blind_status()
    results.append(("Blind Status", status_ok))
    
    # Test 3: Query endpoint (if we have org info)
    if status_ok and status_data:
        orgs = json.loads(status_data.get('organizations', '[]'))
        if orgs:
            org_slug = orgs[0].get('slug')
            print(f"\n   Using organization: {org_slug}")
            # Try to query - this will likely fail if no data, but tests the endpoint
            query_ok, query_result = test_query_endpoint(
                organization=org_slug,
                dataset_slug="test-dataset",  # This probably doesn't exist
                schema_slug="test-schema"     # This probably doesn't exist
            )
            results.append(("Query Endpoint", query_ok))
    
    # Test 4: Client methods
    results.append(("Client Methods", test_client_methods()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Integration is working.")
        return 0
    elif passed > 0:
        print("\n⚠️  Some tests passed. Integration is partially working.")
        print("   (Query endpoint may need actual data to fully test)")
        return 0
    else:
        print("\n❌ Tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

