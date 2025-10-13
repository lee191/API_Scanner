"""Network traffic capture using mitmproxy."""

import json
from typing import List, Set
from mitmproxy import http, ctx
from mitmproxy.tools.main import mitmdump
from urllib.parse import urlparse, parse_qs
from src.utils.models import APIEndpoint, HTTPMethod


class TrafficCapture:
    """Capture and analyze HTTP/HTTPS traffic."""

    def __init__(self):
        """Initialize traffic capture."""
        self.endpoints: List[APIEndpoint] = []
        self.seen_urls: Set[str] = set()
        self.target_domain: str = ""

    def request(self, flow: http.HTTPFlow):
        """Process HTTP request."""
        request = flow.request
        url = request.pretty_url

        # Skip static resources
        if self._is_static_resource(url):
            return

        # Create unique identifier
        endpoint_id = f"{request.method}:{url}"
        if endpoint_id in self.seen_urls:
            return

        self.seen_urls.add(endpoint_id)

        # Extract parameters
        params = {}
        if request.query:
            params.update(dict(request.query))

        # Extract body parameters
        body_example = None
        if request.content:
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    body_example = request.content.decode('utf-8', errors='ignore')
                    body_data = json.loads(body_example)
                    if isinstance(body_data, dict):
                        params.update({k: type(v).__name__ for k, v in body_data.items()})
            except:
                pass

        # Extract headers
        headers = dict(request.headers)

        # Create endpoint
        endpoint = APIEndpoint(
            url=url,
            method=HTTPMethod(request.method),
            parameters=params,
            headers=headers,
            body_example=body_example,
            source="proxy"
        )

        self.endpoints.append(endpoint)
        ctx.log.info(f"[+] Captured: {request.method} {url}")

    def response(self, flow: http.HTTPFlow):
        """Process HTTP response."""
        response = flow.response
        request = flow.request

        # Find corresponding endpoint
        endpoint_id = f"{request.method}:{request.pretty_url}"
        for endpoint in self.endpoints:
            if f"{endpoint.method}:{endpoint.url}" == endpoint_id:
                endpoint.status_code = response.status_code

                # Save response example
                if response.content:
                    try:
                        if response.headers.get("content-type", "").startswith("application/json"):
                            endpoint.response_example = response.content.decode('utf-8', errors='ignore')[:500]
                    except:
                        pass
                break

    def _is_static_resource(self, url: str) -> bool:
        """Check if URL is a static resource."""
        static_extensions = [
            '.css', '.js', '.jpg', '.jpeg', '.png', '.gif',
            '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot',
            '.mp4', '.mp3', '.pdf', '.zip'
        ]

        parsed = urlparse(url)
        path = parsed.path.lower()

        return any(path.endswith(ext) for ext in static_extensions)

    def get_endpoints(self) -> List[APIEndpoint]:
        """Get captured endpoints."""
        return self.endpoints

    def clear(self):
        """Clear captured data."""
        self.endpoints.clear()
        self.seen_urls.clear()


# Global capture instance for mitmproxy addon
capture = TrafficCapture()


def request(flow: http.HTTPFlow):
    """Mitmproxy addon request handler."""
    capture.request(flow)


def response(flow: http.HTTPFlow):
    """Mitmproxy addon response handler."""
    capture.response(flow)


class ProxyRunner:
    """Run proxy server and capture traffic."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        """Initialize proxy runner."""
        self.host = host
        self.port = port
        self.capture = capture

    def start(self):
        """Start proxy server."""
        print(f"[*] Starting proxy on {self.host}:{self.port}")
        print(f"[*] Configure your browser to use this proxy")
        print(f"[*] Press Ctrl+C to stop\n")

        # Run mitmdump with this module as addon
        mitmdump([
            "-s", __file__,
            "--listen-host", self.host,
            "--listen-port", str(self.port),
            "--ssl-insecure"
        ])

    def get_endpoints(self) -> List[APIEndpoint]:
        """Get captured endpoints."""
        return self.capture.get_endpoints()
