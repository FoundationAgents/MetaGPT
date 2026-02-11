#!/usr/bin/env python3
"""
Simple test to verify SSRF fix works without dependencies
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from metagpt.utils.common import is_safe_url

def test_ssrf_fix():
    """Test the SSRF security fix"""
    print("Testing SSRF security fix...")
    
    # Should be safe - public URLs
    safe_urls = [
        "https://example.com/image.jpg",
        "http://www.google.com/logo.png",
    ]
    
    # Should be blocked - internal IPs
    blocked_urls = [
        "http://127.0.0.1:8080/image.jpg",
        "http://localhost/test.png", 
        "http://10.0.0.1/secret.gif",
        "http://169.254.169.254/metadata",
    ]
    
    # Test safe URLs
    print("\nTesting safe URLs:")
    for url in safe_urls:
        result = is_safe_url(url)
        print(f"  {url}: {'✓ SAFE' if result else '✗ BLOCKED'}")
        assert result, f"Public URL should be safe: {url}"
    
    # Test blocked URLs  
    print("\nTesting blocked URLs:")
    for url in blocked_urls:
        result = is_safe_url(url)
        print(f"  {url}: {'✗ BLOCKED' if not result else '✓ SAFE'}")
        assert not result, f"Internal URL should be blocked: {url}"
    
    print("\n✅ All tests passed! SSRF vulnerability is fixed.")

if __name__ == "__main__":
    test_ssrf_fix()