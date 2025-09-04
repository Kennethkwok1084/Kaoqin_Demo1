#!/usr/bin/env python3
"""
Test script to verify TrustedHostMiddleware fix
Tests that endpoints no longer return 400 Bad Request due to host header issues
"""

import os
import sys
sys.path.insert(0, '.')

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['TESTING'] = 'true'
os.environ['DEBUG'] = 'false'

from fastapi.testclient import TestClient
from app.main import app

def test_trusted_host_fix():
    """Test that TrustedHostMiddleware allows testserver"""
    client = TestClient(app)
    
    # Test health endpoint - should not return 400
    response = client.get('/health')
    print(f'Health endpoint: {response.status_code}')
    assert response.status_code != 400, f"Health endpoint returned 400: {response.text}"
    
    # Test auth login endpoint - should not return 400 (may return 500 due to DB)
    login_data = {'student_id': 'test', 'password': 'test'}
    response = client.post('/api/v1/auth/login', json=login_data)
    print(f'Login endpoint: {response.status_code}')
    assert response.status_code != 400, f"Login endpoint returned 400: {response.text}"
    
    print("✅ TrustedHostMiddleware fix verified - no more 400 errors!")
    return True

if __name__ == "__main__":
    test_trusted_host_fix()