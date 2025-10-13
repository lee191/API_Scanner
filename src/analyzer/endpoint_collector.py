"""Endpoint collection and deduplication."""

from typing import List, Dict, Set
from collections import defaultdict
from urllib.parse import urlparse
from src.utils.models import APIEndpoint, HTTPMethod


class EndpointCollector:
    """Collect and deduplicate API endpoints from multiple sources."""

    def __init__(self):
        """Initialize endpoint collector."""
        self.endpoints: List[APIEndpoint] = []
        self.endpoint_map: Dict[str, APIEndpoint] = {}

    def add_endpoint(self, endpoint: APIEndpoint):
        """Add an endpoint with deduplication."""
        # Create unique key
        key = self._create_key(endpoint)

        if key in self.endpoint_map:
            # Merge with existing endpoint
            existing = self.endpoint_map[key]
            existing.parameters.update(endpoint.parameters)
            existing.headers.update(endpoint.headers)

            # Update examples if not present
            if not existing.body_example and endpoint.body_example:
                existing.body_example = endpoint.body_example
            if not existing.response_example and endpoint.response_example:
                existing.response_example = endpoint.response_example

            # Keep most recent timestamp
            if endpoint.timestamp > existing.timestamp:
                existing.timestamp = endpoint.timestamp
        else:
            self.endpoint_map[key] = endpoint
            self.endpoints.append(endpoint)

    def add_endpoints(self, endpoints: List[APIEndpoint]):
        """Add multiple endpoints."""
        for endpoint in endpoints:
            self.add_endpoint(endpoint)

    def _create_key(self, endpoint: APIEndpoint) -> str:
        """Create unique key for endpoint."""
        # Normalize URL by removing query parameters and trailing slashes
        url = endpoint.url.split('?')[0].rstrip('/')
        return f"{endpoint.method}:{url}"

    def get_endpoints(self) -> List[APIEndpoint]:
        """Get all collected endpoints."""
        return self.endpoints

    def get_endpoints_by_method(self, method: HTTPMethod) -> List[APIEndpoint]:
        """Get endpoints filtered by HTTP method."""
        return [ep for ep in self.endpoints if ep.method == method]

    def get_endpoints_by_domain(self, domain: str) -> List[APIEndpoint]:
        """Get endpoints filtered by domain."""
        return [ep for ep in self.endpoints if domain in ep.url]

    def get_statistics(self) -> Dict:
        """Get statistics about collected endpoints."""
        stats = {
            'total': len(self.endpoints),
            'by_method': defaultdict(int),
            'by_source': defaultdict(int),
            'domains': set(),
        }

        for endpoint in self.endpoints:
            stats['by_method'][endpoint.method] += 1
            stats['by_source'][endpoint.source] += 1

            # Extract domain
            try:
                parsed = urlparse(endpoint.url)
                if parsed.netloc:
                    stats['domains'].add(parsed.netloc)
            except:
                pass

        # Convert defaultdict to regular dict and set to list
        stats['by_method'] = dict(stats['by_method'])
        stats['by_source'] = dict(stats['by_source'])
        stats['domains'] = list(stats['domains'])

        return stats

    def filter_by_pattern(self, pattern: str) -> List[APIEndpoint]:
        """Filter endpoints by URL pattern."""
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        return [ep for ep in self.endpoints if regex.search(ep.url)]

    def group_by_path(self) -> Dict[str, List[APIEndpoint]]:
        """Group endpoints by base path."""
        groups = defaultdict(list)

        for endpoint in self.endpoints:
            try:
                parsed = urlparse(endpoint.url)
                path_parts = parsed.path.split('/')

                # Use first 2-3 path segments as group key
                if len(path_parts) >= 3:
                    group_key = '/'.join(path_parts[:3])
                else:
                    group_key = parsed.path

                groups[group_key].append(endpoint)
            except:
                groups['unknown'].append(endpoint)

        return dict(groups)

    def clear(self):
        """Clear all collected endpoints."""
        self.endpoints.clear()
        self.endpoint_map.clear()
