"""Endpoint validation utility to reduce false positives."""

import requests
from typing import Dict, Optional, Tuple
from src.utils.models import APIEndpoint, HTTPMethod


class EndpointValidator:
    """Validate discovered endpoints by sending actual HTTP requests."""

    def __init__(self, timeout: int = 5):
        """
        Initialize endpoint validator.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()

        # Disable SSL warnings for testing
        requests.packages.urllib3.disable_warnings()

    def validate_endpoint(self, endpoint: APIEndpoint) -> Tuple[bool, int, str, Optional[Dict]]:
        """
        Validate if endpoint exists by sending HTTP request.

        Args:
            endpoint: APIEndpoint to validate

        Returns:
            Tuple of (is_valid, status_code, response_snippet, detailed_data)
            - is_valid: True if endpoint exists (not 404)
            - status_code: HTTP response status code
            - response_snippet: First 200 chars of response body
            - detailed_data: Dict containing request/response details for AI analysis
        """
        try:
            # Prepare request
            url = endpoint.url
            method = endpoint.method if isinstance(endpoint.method, str) else endpoint.method.value
            headers = endpoint.headers or {}

            # Add default headers if not present
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Shadow-API-Scanner/1.0'

            # Prepare request parameters
            request_kwargs = {
                'timeout': self.timeout,
                'headers': headers,
                'verify': False,  # Skip SSL verification for testing
                'allow_redirects': False  # Don't follow redirects
            }

            # Add body for POST/PUT/PATCH requests
            request_body = None
            if method in ['POST', 'PUT', 'PATCH']:
                if endpoint.body_example:
                    # Try to use provided body example
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
                    request_kwargs['data'] = endpoint.body_example
                    request_body = endpoint.body_example
                else:
                    # Send minimal valid JSON
                    headers['Content-Type'] = 'application/json'
                    request_kwargs['data'] = '{}'
                    request_body = '{}'

            # Track request time
            import time
            start_time = time.time()
            
            # Send request
            response = self.session.request(method, url, **request_kwargs)
            
            # Calculate response time in milliseconds
            response_time = int((time.time() - start_time) * 1000)

            # Determine if endpoint is valid
            status_code = response.status_code
            is_valid = self._is_valid_status_code(status_code)

            # Get response snippet (first 200 chars)
            response_text = response.text[:200] if response.text else ''
            
            # Prepare detailed data for storage (limit size to avoid bloat)
            response_body_full = response.text[:10000] if response.text else ''  # Max 10KB
            
            detailed_data = {
                'request_headers': dict(headers),
                'request_body': request_body,
                'response_headers': dict(response.headers),
                'response_body': response_body_full,
                'response_time': response_time
            }

            return (is_valid, status_code, response_text, detailed_data)

        except requests.exceptions.Timeout:
            # Timeout might mean endpoint exists but is slow
            return (True, 0, "Request timeout", None)

        except requests.exceptions.ConnectionError:
            # Connection error - endpoint might not exist or server is down
            return (False, 0, "Connection error", None)

        except Exception as e:
            # Other errors - assume invalid
            return (False, 0, f"Error: {str(e)[:100]}", None)

    def _is_valid_status_code(self, status_code: int) -> bool:
        """
        Determine if status code indicates a valid endpoint.

        Args:
            status_code: HTTP status code

        Returns:
            True if endpoint exists, False if it's a false positive
        """
        # 404 = Not Found → False Positive
        if status_code == 404:
            return False

        # 2xx = Success → Valid endpoint
        if 200 <= status_code < 300:
            return True

        # 3xx = Redirect → Valid endpoint (exists but redirects)
        if 300 <= status_code < 400:
            return True

        # 400 = Bad Request → Valid endpoint (exists but needs correct params)
        if status_code == 400:
            return True

        # 401 = Unauthorized → Valid endpoint (exists but needs auth)
        if status_code == 401:
            return True

        # 403 = Forbidden → Valid endpoint (exists but access denied)
        if status_code == 403:
            return True

        # 405 = Method Not Allowed → Valid endpoint (exists but wrong method)
        if status_code == 405:
            return True

        # 422 = Unprocessable Entity → Valid endpoint (exists but validation failed)
        if status_code == 422:
            return True

        # 429 = Too Many Requests → Valid endpoint (exists but rate limited)
        if status_code == 429:
            return True

        # 500 = Internal Server Error → Valid endpoint (exists but has errors)
        if status_code == 500:
            return True

        # Other 5xx errors → Might be valid endpoint with server issues
        if 500 <= status_code < 600:
            return True

        # Default: assume invalid
        return False

    def validate_batch(self, endpoints: list[APIEndpoint],
                      progress_callback=None) -> Dict[str, Tuple[bool, int, str, Optional[Dict]]]:
        """
        Validate multiple endpoints.

        Args:
            endpoints: List of APIEndpoints to validate
            progress_callback: Optional callback function(current, total)

        Returns:
            Dict mapping endpoint URL to (is_valid, status_code, response_snippet, detailed_data)
        """
        results = {}
        total = len(endpoints)

        for i, endpoint in enumerate(endpoints):
            # Validate endpoint
            is_valid, status_code, response, detailed_data = self.validate_endpoint(endpoint)

            # Store result
            key = f"{endpoint.method.value}:{endpoint.url}"
            results[key] = (is_valid, status_code, response, detailed_data)

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def close(self):
        """Close the HTTP session."""
        self.session.close()
