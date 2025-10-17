"""API classification utility to distinguish Shadow APIs from Public APIs."""

import re
from typing import Dict, Optional
from src.utils.models import APIEndpoint


class APIClassifier:
    """
    Classify endpoints as Shadow API or Public API based on multiple criteria.

    Shadow API indicators:
    - URL patterns: /internal, /admin, /debug, /private
    - Sensitive operations: DELETE, PUT on critical resources
    - Authentication requirements with sensitive paths
    - Undocumented endpoints with sensitive data
    """

    # Shadow API URL patterns
    SHADOW_PATTERNS = [
        r'/api/internal/',
        r'/api/admin/',
        r'/api/private/',
        r'/api/debug/',
        r'/internal/',
        r'/admin/',
        r'/debug/',
        r'/private/',
        r'/backup/',
        r'/config',
        r'/console',
        r'/execute',
        r'/exec',
        r'/_',  # Underscore-prefixed paths
        r'/\.well-known/',  # Hidden paths
        r'/api/.*/internal/',  # Versioned internal APIs
        r'/api/.*/admin/',  # Versioned admin APIs
        r'/api/.*/debug/',  # Versioned debug APIs
    ]

    # Public API URL patterns
    PUBLIC_PATTERNS = [
        r'/api/v\d+/auth/',  # Public authentication endpoints
        r'/api/v\d+/users/?$',  # Public user listing (without params)
        r'/api/v\d+/products',  # Public product endpoints
        r'/api/v\d+/search',  # Public search
        r'/api/v\d+/posts',  # Public posts
        r'/api/v\d+/comments',  # Public comments
        r'/api/public/',  # Explicitly public APIs
        r'/login$',  # Public login page
        r'/register$',  # Public registration
        r'/signup$',  # Public signup
    ]

    # Sensitive endpoints (likely Shadow API even if public-looking)
    SENSITIVE_OPERATIONS = {
        'DELETE': ['/users/', '/admin/', '/config', '/database', '/backup'],
        'PUT': ['/admin/', '/config', '/settings', '/roles', '/permissions'],
        'POST': ['/execute', '/exec', '/eval', '/upload', '/backup', '/restore']
    }

    @staticmethod
    def classify(endpoint: APIEndpoint, source: str = None) -> bool:
        """
        Classify an endpoint as Shadow API (True) or Public API (False).

        Args:
            endpoint: APIEndpoint to classify
            source: Source of the endpoint (documentation, openapi, js_analysis, etc.)

        Returns:
            True if Shadow API, False if Public API
        """
        url = endpoint.url.lower()
        method = endpoint.method if isinstance(endpoint.method, str) else endpoint.method.value

        # 1. Check if from official documentation (likely public)
        if source and source.lower() in ['documentation', 'openapi', 'swagger', 'raml']:
            # Even documented APIs can be shadow if they match patterns
            if APIClassifier._matches_shadow_patterns(url):
                return True
            return False

        # 2. Check explicit shadow patterns
        if APIClassifier._matches_shadow_patterns(url):
            return True

        # 3. Check explicit public patterns
        if APIClassifier._matches_public_patterns(url):
            # But still check for sensitive operations
            if APIClassifier._is_sensitive_operation(url, method):
                return True
            return False

        # 4. Check sensitive operations
        if APIClassifier._is_sensitive_operation(url, method):
            return True

        # 5. Check response indicators (if available)
        if endpoint.status_code:
            if APIClassifier._check_response_indicators(endpoint):
                return True

        # 6. Default: if no clear public indicator, treat as shadow (conservative)
        # This is safer for security scanning
        return True

    @staticmethod
    def _matches_shadow_patterns(url: str) -> bool:
        """Check if URL matches shadow API patterns."""
        for pattern in APIClassifier.SHADOW_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def _matches_public_patterns(url: str) -> bool:
        """Check if URL matches public API patterns."""
        for pattern in APIClassifier.PUBLIC_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def _is_sensitive_operation(url: str, method: str) -> bool:
        """Check if the operation is sensitive based on method and URL."""
        if method not in APIClassifier.SENSITIVE_OPERATIONS:
            return False

        sensitive_paths = APIClassifier.SENSITIVE_OPERATIONS[method]
        for path in sensitive_paths:
            if path in url:
                return True
        return False

    @staticmethod
    def _check_response_indicators(endpoint: APIEndpoint) -> bool:
        """Check response for shadow API indicators."""
        # 401/403 with admin/internal paths are likely shadow
        if endpoint.status_code in [401, 403]:
            url = endpoint.url.lower()
            if any(keyword in url for keyword in ['admin', 'internal', 'debug', 'private']):
                return True

        # Check response content for sensitive data
        if endpoint.response_example:
            sensitive_keywords = [
                'password', 'api_key', 'secret', 'token',
                'private', 'credential', 'ssn', 'credit_card'
            ]
            response_lower = endpoint.response_example.lower()
            for keyword in sensitive_keywords:
                if keyword in response_lower:
                    return True

        return False

    @staticmethod
    def get_classification_reason(endpoint: APIEndpoint, source: str = None) -> str:
        """
        Get human-readable reason for classification.

        Args:
            endpoint: APIEndpoint to classify
            source: Source of the endpoint

        Returns:
            Reason string explaining the classification
        """
        url = endpoint.url.lower()
        method = endpoint.method if isinstance(endpoint.method, str) else endpoint.method.value

        # Check each criterion
        if source and source.lower() in ['documentation', 'openapi', 'swagger']:
            if APIClassifier._matches_shadow_patterns(url):
                return "Documented but contains shadow patterns (internal/admin/debug)"
            return "From official documentation"

        if APIClassifier._matches_shadow_patterns(url):
            for pattern in APIClassifier.SHADOW_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    return f"Matches shadow pattern: {pattern}"

        if APIClassifier._matches_public_patterns(url):
            if APIClassifier._is_sensitive_operation(url, method):
                return f"Public endpoint but sensitive operation: {method}"
            return "Matches public API pattern"

        if APIClassifier._is_sensitive_operation(url, method):
            return f"Sensitive operation: {method} on sensitive path"

        if endpoint.status_code:
            if APIClassifier._check_response_indicators(endpoint):
                return "Response contains sensitive data or requires high-level auth"

        return "Default classification (no public indicators found)"


def classify_endpoints_by_status(endpoints: list) -> Dict[str, list]:
    """
    Classify endpoints by HTTP status code.

    Args:
        endpoints: List of APIEndpoint objects

    Returns:
        Dictionary with endpoints grouped by status code category
    """
    categorized = {
        'success': [],      # 2xx
        'redirect': [],     # 3xx
        'client_error': [], # 4xx
        'server_error': [], # 5xx
        'unknown': []       # No status code or other
    }

    for endpoint in endpoints:
        status = endpoint.status_code if hasattr(endpoint, 'status_code') else None
        
        if status is None:
            categorized['unknown'].append(endpoint)
        elif 200 <= status < 300:
            categorized['success'].append(endpoint)
        elif 300 <= status < 400:
            categorized['redirect'].append(endpoint)
        elif 400 <= status < 500:
            categorized['client_error'].append(endpoint)
        elif 500 <= status < 600:
            categorized['server_error'].append(endpoint)
        else:
            categorized['unknown'].append(endpoint)

    return categorized


def classify_endpoints(endpoints: list, source: str = None) -> Dict[str, list]:
    """
    Classify endpoints by status code instead of shadow/public.
    Maintains backward compatibility with old structure.

    Args:
        endpoints: List of APIEndpoint objects
        source: Source of the endpoints (kept for compatibility)

    Returns:
        Dictionary with endpoint categorization by status
    """
    categorized = classify_endpoints_by_status(endpoints)
    
    # For backward compatibility, still provide shadow_apis/public_apis
    # But now based on status codes
    shadow_apis = categorized['client_error'] + categorized['server_error']
    public_apis = categorized['success'] + categorized['redirect'] + categorized['unknown']

    return {
        'shadow_apis': shadow_apis,  # Errors (4xx, 5xx)
        'public_apis': public_apis,  # Success/Redirect (2xx, 3xx, unknown)
        'by_status': categorized     # New: detailed status categorization
    }
