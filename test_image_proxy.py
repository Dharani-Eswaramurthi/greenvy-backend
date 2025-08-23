#!/usr/bin/env python3
"""
Test script to verify image proxy functionality
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
TEST_IMAGE_PATH = "product-images/zero-waste-biodegradable/100ml-cups/image1.jpg"  # Example image path

def test_image_proxy_with_allowed_domain():
    """Test image proxy with allowed domain (localhost:3000)"""
    print("Testing image proxy with allowed domain...")
    
    headers = {
        "Referer": "http://localhost:3000/test-page",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/images/{TEST_IMAGE_PATH}", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Image accessed successfully with allowed domain")
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_image_proxy_with_disallowed_domain():
    """Test image proxy with disallowed domain"""
    print("\nTesting image proxy with disallowed domain...")
    
    headers = {
        "Referer": "http://malicious-site.com/test-page",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/images/{TEST_IMAGE_PATH}", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SUCCESS: Access denied for disallowed domain")
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_image_proxy_without_referer():
    """Test image proxy without referer header"""
    print("\nTesting image proxy without referer header...")
    
    try:
        response = requests.get(f"{BASE_URL}/images/{TEST_IMAGE_PATH}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ SUCCESS: Access denied without referer header")
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_greenvy_store_domain():
    """Test image proxy with greenvy.store domain"""
    print("\nTesting image proxy with greenvy.store domain...")
    
    headers = {
        "Referer": "https://greenvy.store/product-page",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/images/{TEST_IMAGE_PATH}", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Image accessed successfully with greenvy.store domain")
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_nonexistent_image():
    """Test image proxy with nonexistent image"""
    print("\nTesting image proxy with nonexistent image...")
    
    headers = {
        "Referer": "http://localhost:3000/test-page",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/images/nonexistent/image.jpg", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ SUCCESS: 404 returned for nonexistent image")
        else:
            print(f"❌ FAILED: Expected 404, got {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing Image Proxy Functionality")
    print("=" * 50)
    
    test_image_proxy_with_allowed_domain()
    test_image_proxy_with_disallowed_domain()
    test_image_proxy_without_referer()
    test_greenvy_store_domain()
    test_nonexistent_image()
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")
