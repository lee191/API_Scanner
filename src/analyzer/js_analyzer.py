"""JavaScript static analysis to extract API endpoints."""

import re
import json
from typing import List, Set, Dict
from pathlib import Path
from urllib.parse import urljoin, urlparse
import esprima
from bs4 import BeautifulSoup
from src.utils.models import APIEndpoint, HTTPMethod

# Try to import AI analyzer (optional)
try:
    from src.analyzer.ai_analyzer import AIJSAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("[!] AI Analyzer not available. Install openai package: pip install openai")


class JSAnalyzer:
    """Analyze JavaScript files to extract API endpoints."""

    def __init__(self, use_ai: bool = True):
        """
        Initialize JS analyzer.

        Args:
            use_ai: Enable AI-powered analysis (default: True)
        """
        self.endpoints: List[APIEndpoint] = []
        self.seen_urls: Set[str] = set()
        self.use_ai = use_ai and AI_AVAILABLE

        # Initialize AI analyzer if available
        if self.use_ai:
            try:
                self.ai_analyzer = AIJSAnalyzer()
                if self.ai_analyzer.enabled:
                    print("[+] AI-powered JS analysis enabled")
                else:
                    self.use_ai = False
            except Exception as e:
                print(f"[!] Failed to initialize AI analyzer: {e}")
                self.use_ai = False

        # Common API patterns
        self.api_patterns = [
            # fetch API
            r'fetch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'fetch\s*\(\s*`([^`]+)`',

            # axios
            r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'axios\s*\(\s*{\s*url:\s*[\'"`]([^\'"` ]+)[\'"`]',

            # XMLHttpRequest
            r'\.open\s*\(\s*[\'"`](GET|POST|PUT|DELETE|PATCH)[\'"`]\s*,\s*[\'"`]([^\'"` ]+)[\'"`]',

            # jQuery
            r'\$\.(get|post|ajax)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',

            # URL strings
            r'[\'"`](/api/[^\'"` ]+)[\'"`]',
            r'[\'"`](https?://[^\'"` ]+)[\'"`]',
        ]

    def analyze_file(self, file_path: str, base_url: str = "") -> List[APIEndpoint]:
        """Analyze a JavaScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Use regex-based analysis
            endpoints = self.analyze_content(content, base_url, source=file_path)

            # Enhance with AI if enabled
            if self.use_ai and len(content) > 100:  # Only use AI for substantial files
                try:
                    print(f"[AI] Analyzing {file_path}...")
                    ai_endpoints = self.ai_analyzer.analyze_js_code(content, file_path, base_url)

                    # Merge AI results with regex results
                    for ai_ep in ai_endpoints:
                        endpoint_id = f"{ai_ep.method}:{ai_ep.url}"
                        if endpoint_id not in self.seen_urls:
                            self.seen_urls.add(endpoint_id)
                            endpoints.append(ai_ep)
                            print(f"  [AI] Found: {ai_ep.method} {ai_ep.url}")
                except Exception as e:
                    print(f"[!] AI analysis error: {e}")

            return endpoints

        except Exception as e:
            print(f"[!] Error analyzing {file_path}: {e}")
            return []

    def analyze_content(self, content: str, base_url: str = "", source: str = "js_analysis") -> List[APIEndpoint]:
        """Analyze JavaScript content."""
        endpoints = []

        # Extract URLs using regex patterns
        for pattern in self.api_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    # Determine method and URL based on pattern
                    if len(match.groups()) == 2:
                        method_or_url = match.group(1)
                        url = match.group(2) if len(match.groups()) > 1 else match.group(1)

                        # Check if first group is a method
                        if method_or_url.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            method = HTTPMethod(method_or_url.upper())
                        else:
                            url = method_or_url
                            method = HTTPMethod.GET
                    else:
                        url = match.group(1)
                        method = HTTPMethod.GET

                    # Skip if URL contains template variables
                    if '${' in url or '{' in url:
                        # Extract base URL without template variables
                        url = re.sub(r'\$\{[^}]+\}', ':param', url)
                        url = re.sub(r'\{[^}]+\}', ':param', url)

                    # Make absolute URL
                    if url.startswith('/') and base_url:
                        url = urljoin(base_url, url)

                    # Skip non-API URLs
                    if not self._is_api_url(url):
                        continue

                    # Create unique identifier
                    endpoint_id = f"{method}:{url}"
                    if endpoint_id in self.seen_urls:
                        continue

                    self.seen_urls.add(endpoint_id)

                    # Extract parameters from URL
                    params = self._extract_params_from_url(url)

                    endpoint = APIEndpoint(
                        url=url,
                        method=method,
                        parameters=params,
                        source=source
                    )

                    endpoints.append(endpoint)

                except Exception as e:
                    continue

        # Try to parse with esprima for more accurate analysis
        try:
            endpoints.extend(self._analyze_with_esprima(content, base_url, source))
        except:
            pass

        return endpoints

    def _analyze_with_esprima(self, content: str, base_url: str, source: str) -> List[APIEndpoint]:
        """Analyze using esprima AST parser."""
        endpoints = []

        try:
            tree = esprima.parseScript(content, {'tolerant': True})
            # Additional AST-based analysis can be added here
        except:
            pass

        return endpoints

    def _is_api_url(self, url: str) -> bool:
        """Check if URL looks like an API endpoint."""
        api_indicators = [
            '/api/', '/v1/', '/v2/', '/v3/',
            '/rest/', '/graphql', '/data/',
            '/service/', '/backend/'
        ]

        url_lower = url.lower()
        return any(indicator in url_lower for indicator in api_indicators) or \
               url_lower.startswith('http')

    def _extract_params_from_url(self, url: str) -> Dict[str, str]:
        """Extract parameters from URL."""
        params = {}

        # Extract query parameters
        if '?' in url:
            query = url.split('?')[1]
            for param in query.split('&'):
                if '=' in param:
                    key = param.split('=')[0]
                    params[key] = "string"

        # Extract path parameters
        path_params = re.findall(r':(\w+)', url)
        for param in path_params:
            params[param] = "path_param"

        return params

    def analyze_html(self, html_content: str, base_url: str = "") -> List[APIEndpoint]:
        """Extract and analyze JavaScript from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        endpoints = []

        # Find all script tags
        for script in soup.find_all('script'):
            if script.string:
                endpoints.extend(self.analyze_content(script.string, base_url, "html_inline"))

            # External scripts
            if script.get('src'):
                src = script['src']
                if base_url and not src.startswith('http'):
                    src = urljoin(base_url, src)
                # Note: Would need to fetch external scripts

        return endpoints

    def get_endpoints(self) -> List[APIEndpoint]:
        """Get all discovered endpoints."""
        return self.endpoints

    def clear(self):
        """Clear analyzed data."""
        self.endpoints.clear()
        self.seen_urls.clear()
