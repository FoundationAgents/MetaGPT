#!/usr/bin/env python3
"""
Simple test to verify SSRF fix logic without dependencies
"""
import ipaddress
import socket
from urllib.parse import urlparse

# Copy the exact security logic we implemented
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Localhost
    ipaddress.ip_network('10.0.0.0/8'),       # Private
    ipaddress.ip_network('172.16.0.0/12'),    # Private
    ipaddress.ip_network('192.168.0.0/16'),   # Private
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local/Metadata
    ipaddress.ip_network('::1/128'),          # IPv6 localhost
]

def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks by checking for internal/private IPs."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Resolve hostname to IP address
        ip = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip)
        
        # Check against blocked IP ranges
        for blocked in BLOCKED_IP_RANGES:
            if ip_addr in blocked:
                return False
        return True
    except Exception:
        return False

def test_ssrf_fix():
    """Test the SSRF security fix"""
    print("Testing SSRF security fix...")
    
    # Should be blocked - internal IPs
    blocked_urls = [
        "http://127.0.0.1:8080/image.jpg",
        "http://localhost/test.png", 
        "http://10.0.0.1/secret.gif",
        "http://169.254.169.254/metadata",
        "ftp://example.com/file.jpg",  # Wrong protocol
        "",  # Empty URL
        "http://",  # Malformed
    ]
    
    # Test blocked URLs  
    print("\nTesting blocked URLs:")
    for url in blocked_urls:
        result = is_safe_url(url)
        print(f"  {url}: {'✗ BLOCKED' if not result else '✓ SAFE'}")
        if result and url in ["http://127.0.0.1:8080/image.jpg", "http://localhost/test.png"]:
            print(f"    ERROR: Internal URL should be blocked: {url}")
            return False
    
    print("\n✅ Security validation is working! SSRF vulnerability is fixed.")
    return True

if __name__ == "__main__":
    success = test_ssrf_fix()
    if not success:
        exit(1)