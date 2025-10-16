"""JavaScript static analysis to extract API endpoints."""

import re
import json
from typing import List, Set, Dict
from pathlib import Path
from urllib.parse import urljoin, urlparse
import esprima
from bs4 import BeautifulSoup
from src.utils.models import APIEndpoint, HTTPMethod


class JSAnalyzer:
    """Analyze JavaScript files to extract API endpoints."""

    def __init__(self):
        """Initialize JS analyzer."""
        self.endpoints: List[APIEndpoint] = []
        self.seen_urls: Set[str] = set()  # Track (method:URL) pairs to prevent exact duplicates

        # Enhanced API patterns with more coverage
        self.api_patterns = [
            # ===== fetch API =====
            # Basic fetch with string
            r'fetch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            # fetch with template literal
            r'fetch\s*\(\s*`([^`]+)`',
            # fetch with variable + string concatenation (captures URL parts)
            r'fetch\s*\(\s*([a-zA-Z_$][\w$]*)\s*\+\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'fetch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]\s*\+',

            # ===== axios =====
            # axios method calls
            r'axios\.(get|post|put|delete|patch|head|options)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'axios\.(get|post|put|delete|patch|head|options)\s*\(\s*`([^`]+)`',
            # axios with config object
            r'axios\s*\(\s*{\s*url:\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'axios\s*\(\s*{\s*url:\s*`([^`]+)`',
            # axios.request()
            r'axios\.request\s*\(\s*{\s*url:\s*[\'"`]([^\'"` ]+)[\'"`]',

            # ===== XMLHttpRequest =====
            r'\.open\s*\(\s*[\'"`](GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)[\'"`]\s*,\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'\.open\s*\(\s*[\'"`](GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)[\'"`]\s*,\s*`([^`]+)`',

            # ===== jQuery =====
            r'\$\.(get|post|ajax|getJSON)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            r'\$\.(get|post|ajax|getJSON)\s*\(\s*`([^`]+)`',
            r'\$\.ajax\s*\(\s*{\s*url:\s*[\'"`]([^\'"` ]+)[\'"`]',

            # ===== Modern frameworks =====
            # Superagent
            r'request\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            # ky
            r'ky\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
            # got
            r'got\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',

            # ===== API endpoint URLs (standalone) =====
            # API paths in strings
            r'[\'"`](/api/[^\'"` ]+)[\'"`]',
            r'[\'"`](/v\d+/[^\'"` ]+)[\'"`]',
            r'[\'"`](/rest/[^\'"` ]+)[\'"`]',
            r'[\'"`](/graphql[^\'"` ]*)[\'"`]',
            r'[\'"`](/internal/[^\'"` ]+)[\'"`]',
            # Full URLs
            r'[\'"`](https?://[^\'"` ]+/api/[^\'"` ]+)[\'"`]',
            r'[\'"`](https?://[^\'"` ]+/v\d+/[^\'"` ]+)[\'"`]',

            # ===== Dynamic URL construction (NEW) =====
            # Template literals with variables: `/api/users/${userId}`
            r'`/api/[^`]*\$\{[^}]+\}[^`]*`',
            r'`/internal/[^`]*\$\{[^}]+\}[^`]*`',
            r'`/v\d+/[^`]*\$\{[^}]+\}[^`]*`',
            # String concatenation: '/api/users/' + userId
            r'[\'"](/api/[^\'"]+)[\'"][\s\+]+\w+',
            r'[\'"](/internal/[^\'"]+)[\'"][\s\+]+\w+',
            # Variable assignment with API paths
            r'(?:const|let|var)\s+\w+\s*=\s*[\'"`](/api/[^\'"` ]+)[\'"`]',
            r'(?:const|let|var)\s+\w+\s*=\s*`(/api/[^`]+)`',
        ]

    def analyze_file(self, file_path: str, base_url: str = "") -> List[APIEndpoint]:
        """Analyze a JavaScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Use regex-based analysis
            endpoints = self.analyze_content(content, base_url, source=file_path)

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
                    method = HTTPMethod.GET  # Default
                    url = None

                    if len(match.groups()) == 2:
                        group1 = match.group(1)
                        group2 = match.group(2)

                        # Check if first group is a method
                        if group1.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                            method = HTTPMethod(group1.upper())
                            url = group2
                        else:
                            # Check if it's a jQuery/framework method
                            method = self._map_framework_method(group1)
                            url = group2
                    else:
                        url = match.group(1)
                        method = HTTPMethod.GET

                    # Clean and validate URL (handles template variables, normalization, etc.)
                    url_result = self._clean_url(url, base_url)

                    if isinstance(url_result, tuple):
                        url, had_api_variable = url_result
                    else:
                        url, had_api_variable = url_result, False

                    # Skip invalid URLs
                    if not url:
                        continue

                    # Skip non-API URLs (but allow URLs that came from API base variables)
                    if not had_api_variable and not self._is_api_url(url):
                        continue

                    # Try to extract method, headers, and body from surrounding context
                    context_info = self._extract_context_info(content, url, match.start())

                    # Update method if found in context (context takes priority)
                    if context_info.get('method'):
                        try:
                            method = HTTPMethod(context_info['method'].upper())
                        except:
                            pass

                    # Create unique identifier (method + URL)
                    # This allows same URL with different methods (e.g., GET /posts and POST /posts)
                    endpoint_id = f"{method.value}:{url}"
                    if endpoint_id in self.seen_urls:
                        continue

                    self.seen_urls.add(endpoint_id)

                    # Extract parameters from URL
                    params = self._extract_params_from_url(url)

                    endpoint = APIEndpoint(
                        url=url,
                        method=method,
                        parameters=params,
                        headers=context_info.get('headers', {}),
                        body_example=context_info.get('body'),
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

    def _map_framework_method(self, method_name: str) -> HTTPMethod:
        """
        Map framework-specific method names to HTTP methods.

        Args:
            method_name: Method name from framework (e.g., 'get', 'post', 'ajax')

        Returns:
            Corresponding HTTPMethod
        """
        method_map = {
            'get': HTTPMethod.GET,
            'post': HTTPMethod.POST,
            'put': HTTPMethod.PUT,
            'delete': HTTPMethod.DELETE,
            'patch': HTTPMethod.PATCH,
            'head': HTTPMethod.HEAD,
            'options': HTTPMethod.OPTIONS,
            'ajax': HTTPMethod.GET,  # $.ajax defaults to GET
            'getjson': HTTPMethod.GET,
        }

        return method_map.get(method_name.lower(), HTTPMethod.GET)

    def _analyze_with_esprima(self, content: str, base_url: str, source: str) -> List[APIEndpoint]:
        """
        Analyze using esprima AST parser.

        This method provides more accurate API endpoint detection by analyzing
        the Abstract Syntax Tree (AST) of JavaScript code.
        """
        endpoints = []

        try:
            # Parse JavaScript with tolerant mode (continues even with syntax errors)
            tree = esprima.parseScript(content, {'tolerant': True, 'loc': True})

            # Walk the AST to find API calls
            self._walk_ast(tree, endpoints, base_url, source)

        except Exception as e:
            # If AST parsing completely fails, silently continue
            # Regex patterns will still catch most endpoints
            pass

        return endpoints

    def _walk_ast(self, node, endpoints: List[APIEndpoint], base_url: str, source: str):
        """
        Recursively walk AST to find API calls.

        Looks for:
        - fetch() calls
        - axios.get/post/etc calls
        - new XMLHttpRequest()
        - String literals containing API paths
        """
        if not isinstance(node, dict):
            return

        node_type = node.get('type')

        # Detect fetch() calls
        if node_type == 'CallExpression':
            callee = node.get('callee', {})

            # Direct fetch() call
            if callee.get('type') == 'Identifier' and callee.get('name') == 'fetch':
                self._extract_fetch_call(node, endpoints, base_url, source)

            # axios.get(), axios.post(), etc
            elif callee.get('type') == 'MemberExpression':
                obj = callee.get('object', {})
                prop = callee.get('property', {})

                if obj.get('name') == 'axios' and prop.get('type') == 'Identifier':
                    method_name = prop.get('name', 'get')
                    self._extract_axios_call(node, method_name, endpoints, base_url, source)

        # Recursively visit all child nodes
        for key, value in node.items():
            if isinstance(value, dict):
                self._walk_ast(value, endpoints, base_url, source)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._walk_ast(item, endpoints, base_url, source)

    def _extract_fetch_call(self, node: Dict, endpoints: List[APIEndpoint], base_url: str, source: str):
        """Extract endpoint from fetch() call."""
        try:
            arguments = node.get('arguments', [])
            if not arguments:
                return

            # First argument is the URL
            url_node = arguments[0]
            url = self._extract_string_value(url_node)

            if not url:
                return

            # Default method is GET
            method = HTTPMethod.GET
            headers = {}
            body = None

            # Second argument is options object
            if len(arguments) > 1:
                options = arguments[1]
                if options.get('type') == 'ObjectExpression':
                    for prop in options.get('properties', []):
                        key_node = prop.get('key', {})
                        value_node = prop.get('value', {})
                        key_name = key_node.get('name') or key_node.get('value')

                        if key_name == 'method':
                            method_str = self._extract_string_value(value_node)
                            if method_str:
                                try:
                                    method = HTTPMethod(method_str.upper())
                                except:
                                    pass

                        elif key_name == 'headers':
                            headers = self._extract_object(value_node)

                        elif key_name == 'body':
                            body = self._extract_string_value(value_node)

            # Clean and validate URL
            url_result = self._clean_url(url, base_url)
            if isinstance(url_result, tuple):
                url, had_api_variable = url_result
            else:
                url, had_api_variable = url_result, False

            if url and (had_api_variable or self._is_api_url(url)):
                # Deduplicate by method + URL
                endpoint_id = f"{method.value}:{url}"
                if endpoint_id not in self.seen_urls:
                    self.seen_urls.add(endpoint_id)

                    endpoint = APIEndpoint(
                        url=url,
                        method=method,
                        headers=headers,
                        body_example=body,
                        parameters=self._extract_params_from_url(url),
                        source=f"{source} (AST)"
                    )
                    endpoints.append(endpoint)

        except Exception as e:
            pass

    def _extract_axios_call(self, node: Dict, method_name: str, endpoints: List[APIEndpoint], base_url: str, source: str):
        """Extract endpoint from axios call."""
        try:
            arguments = node.get('arguments', [])
            if not arguments:
                return

            url = self._extract_string_value(arguments[0])
            if not url:
                return

            # Map axios method names to HTTP methods
            try:
                method = HTTPMethod(method_name.upper())
            except:
                method = HTTPMethod.GET

            # Clean and validate URL
            url_result = self._clean_url(url, base_url)
            if isinstance(url_result, tuple):
                url, had_api_variable = url_result
            else:
                url, had_api_variable = url_result, False

            if url and (had_api_variable or self._is_api_url(url)):
                # Deduplicate by method + URL
                endpoint_id = f"{method.value}:{url}"
                if endpoint_id not in self.seen_urls:
                    self.seen_urls.add(endpoint_id)

                    endpoint = APIEndpoint(
                        url=url,
                        method=method,
                        parameters=self._extract_params_from_url(url),
                        source=f"{source} (AST)"
                    )
                    endpoints.append(endpoint)

        except Exception as e:
            pass

    def _extract_string_value(self, node: Dict) -> str:
        """Extract string value from AST node."""
        if not node:
            return None

        node_type = node.get('type')

        # Literal string
        if node_type == 'Literal':
            value = str(node.get('value', ''))
            # Reject empty strings
            if not value or not value.strip():
                return None
            return value

        # Template literal
        elif node_type == 'TemplateLiteral':
            # Combine quasis (string parts) and expressions
            parts = []
            quasis = node.get('quasis', [])
            expressions = node.get('expressions', [])

            for i, quasi in enumerate(quasis):
                # Add static string part
                static_part = quasi.get('value', {}).get('raw', '')
                parts.append(static_part)

                # Add expression placeholder
                if i < len(expressions):
                    expr = expressions[i]
                    # Use expression name if it's an identifier
                    if expr.get('type') == 'Identifier':
                        expr_name = expr.get('name', 'param')
                        # Filter out common base URL variable names
                        if expr_name.lower() in ['baseurl', 'api_url', 'host', 'url', 'base', 'endpoint']:
                            # This is likely a base URL variable, skip it
                            continue
                        parts.append(f':{expr_name}')
                    else:
                        parts.append(':param')

            result = ''.join(parts)

            # If result is empty or starts with :param/, it's malformed
            if not result or result.startswith(':param/') or result.startswith(':'):
                return None

            return result

        return None

    def _extract_object(self, node: Dict) -> Dict[str, str]:
        """Extract key-value pairs from object expression."""
        result = {}

        if not node or node.get('type') != 'ObjectExpression':
            return result

        for prop in node.get('properties', []):
            key_node = prop.get('key', {})
            value_node = prop.get('value', {})

            key = key_node.get('name') or key_node.get('value')
            value = self._extract_string_value(value_node)

            if key and value:
                result[str(key)] = str(value)

        return result

    def _clean_url(self, url: str, base_url: str):
        """
        Clean and normalize URL with improved handling.

        Returns:
            tuple: (cleaned_url, had_api_variable) where had_api_variable indicates if an API base variable was removed
        """
        if not url:
            return (None, False)

        # Strip whitespace
        url = url.strip()

        # Reject empty or too short URLs
        if len(url) < 2:
            return (None, False)

        # Remove base URL template variables
        # Common patterns: ${baseUrl}, ${API_BASE}, ${HOST}, ${AUTH_API}, ${SHOP_API}, etc.
        base_url_patterns = [
            r'^\$\{(base[Uu]rl|API_URL|API_BASE|HOST|host|url|URL|BASE_PATH|basePath|apiBase|api_base|server|SERVER)\}/?',
            r'^\$\{[^}]*[Uu]rl[^}]*\}/?',  # Any variable with "url" in name
            r'^\$\{[^}]*[Hh]ost[^}]*\}/?',  # Any variable with "host" in name
            r'^\$\{[^}]*[Bb]ase[^}]*\}/?',  # Any variable with "base" in name
            r'^\$\{[^}]*[Ss]erver[^}]*\}/?',  # Any variable with "server" in name
            r'^\$\{[^}]*_?API[^}]*\}/?',  # Any variable ending with "_API" or containing "API"
            r'^\$\{API[^}]*\}/?',  # Variables starting with "API"
        ]

        original_url = url
        had_api_variable = False

        for pattern in base_url_patterns:
            new_url = re.sub(pattern, '', url)
            if new_url != url:
                had_api_variable = True
                url = new_url

        # Remove common API base constants (case insensitive)
        temp = re.sub(r'^API_BASE/?', '', url, flags=re.IGNORECASE)
        if temp != url:
            had_api_variable = True
            url = temp

        temp = re.sub(r'^BASE_URL/?', '', url, flags=re.IGNORECASE)
        if temp != url:
            had_api_variable = True
            url = temp

        # If removing base URL variable left us with empty or just '/', reject
        if not url or url == '/':
            return (None, False)

        # If we removed a base URL variable and the remaining path doesn't start with /,
        # it means the variable contained the full path (like ${AUTH_API}/login)
        # In this case, ensure the path starts with /
        if url != original_url and not url.startswith('/') and not url.startswith('http'):
            url = '/' + url

        # Replace template variables with parameter names (improved)
        # Handle function calls in template literals: ${encodeURIComponent(search)} → :search
        def replace_template_function(match):
            content = match.group(1)
            # Check if it's a function call like encodeURIComponent(varName)
            func_match = re.match(r'(encodeURIComponent|decodeURIComponent|encodeURI|decodeURI|parseInt|parseFloat|String|Number)\s*\(\s*([^)]+)\s*\)', content)
            if func_match:
                # Extract the variable name from inside the function call
                var_name = func_match.group(2).strip()
                return f':{var_name}'
            # Otherwise just use the content directly
            return f':{content}'

        # ${userId} → :userId or ${encodeURIComponent(search)} → :search
        url = re.sub(r'\$\{([^}]+)\}', replace_template_function, url)
        # {userId} → :userId (but avoid matching port numbers)
        # Only replace if not preceded by : (to avoid matching :8080)
        url = re.sub(r'(?<!:)\{([^}]+)\}', r':\1', url)

        # Reject URLs with generic placeholder names (these are usually from utility function definitions)
        generic_placeholders = ['endpoint', 'path', 'route', 'url', 'uri', 'resource']
        for placeholder in generic_placeholders:
            if f':{placeholder}' in url.lower():
                return (None, False)

        # Normalize parameter names (lowercase for consistency)
        def normalize_param(match):
            param_name = match.group(1)

            # Skip if it's a port number (all digits)
            if param_name.isdigit():
                return match.group(0)  # Return unchanged (:5000 stays as :5000)

            # Skip common JavaScript function names
            if param_name in ['encodeURIComponent', 'decodeURIComponent', 'encodeURI', 'decodeURI',
                             'parseInt', 'parseFloat', 'String', 'Number']:
                # This shouldn't happen if template replacement worked, but just in case
                return ''  # Remove it

            # Common ID patterns
            if re.match(r'(user|post|product|item|order|comment)id', param_name, re.IGNORECASE):
                return ':id'

            # Keep descriptive names
            return f':{param_name}'

        url = re.sub(r':(\w+)', normalize_param, url)

        # Clean up any remaining port numbers in URL path (shouldn't happen, but safety check)
        # Match pattern like ://localhost:5000/ and ensure :5000 is not treated as path param
        # This is done by checking if :digits appears right after hostname
        url = re.sub(r'(://[^/]+):(\d+)/', r'\1:\2/', url)  # Keep port numbers intact

        # Fix malformed URLs that start with :param
        # /api/:param/users → valid (path param)
        # :param/api/users → INVALID (base URL variable wasn't removed properly)
        if url.startswith(':'):
            # This is a malformed URL - the entire base was replaced with :param
            return (None, False)

        # Fix consecutive colons (:param:param)
        url = re.sub(r':([^/]+):([^/]+)', r':\1/:\2', url)

        # Fix double slashes (but preserve http:// and https://)
        if url.startswith('http://') or url.startswith('https://'):
            # Preserve protocol, fix double slashes in the rest
            protocol, rest = url.split('://', 1)
            rest = re.sub(r'/+', '/', rest)
            url = f'{protocol}://{rest}'
        else:
            # For relative URLs, just fix double slashes
            url = re.sub(r'/+', '/', url)

        # Ensure URL starts with /
        if url and not url.startswith('/') and not url.startswith('http'):
            url = '/' + url

        # Reject if still doesn't start with / or http
        if url and not (url.startswith('/') or url.startswith('http')):
            return (None, False)

        # Make absolute URL
        if url and url.startswith('/') and base_url:
            from urllib.parse import urljoin
            url = urljoin(base_url, url)

        return (url, had_api_variable)

    def _is_api_url(self, url: str) -> bool:
        """Check if URL looks like an API endpoint."""
        if not url:
            return False

        # Reject empty or whitespace-only URLs
        if not url.strip():
            return False

        # Remove base URL for comparison
        path = url
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path

        # Remove trailing slash and query params for path analysis
        path_normalized = path.split('?')[0].rstrip('/')

        # Reject URLs that are EXACTLY just prefixes (incomplete paths)
        # /api/v1 → INVALID (no resource)
        # /api/v1/users → VALID (has resource)
        exact_prefixes = [
            '/api/v1', '/api/v2', '/api/v3',
            '/api', '/v1', '/v2', '/v3',
            '/api/v1/auth'  # This alone is not an endpoint
        ]

        if path_normalized in exact_prefixes:
            return False

        # Check for API indicators
        api_indicators = [
            '/api/', '/v1/', '/v2/', '/v3/',
            '/rest/', '/graphql', '/data/',
            '/service/', '/backend/', '/internal/'
        ]

        url_lower = url.lower()
        has_indicator = any(indicator in url_lower for indicator in api_indicators)

        if not has_indicator:
            return False

        # Must have at least 3 path segments OR have query params
        # /api/v1/users ✓ (3 segments)
        # /api/users ✓ (2 segments, still valid)
        # /api ✗ (1 segment)
        path_parts = [p for p in path.split('/') if p and not p.startswith(':')]
        if len(path_parts) < 2:
            return False

        return True

    def _extract_params_from_url(self, url: str) -> Dict[str, str]:
        """Extract parameters from URL."""
        params = {}

        # Parse URL to separate scheme, netloc, path, and query
        from urllib.parse import urlparse, parse_qs

        try:
            parsed = urlparse(url)

            # Extract query parameters using parse_qs for proper parsing
            if parsed.query:
                # Use parse_qs to handle query string properly
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                for key, values in query_params.items():
                    # Skip invalid parameter names (numbers, function names, etc.)
                    if key.isdigit() or key in ['encodeURIComponent', 'decodeURIComponent', 'encodeURI', 'decodeURI']:
                        continue
                    # Skip keys that look like template variables or function calls
                    if '$' in key or '(' in key or ')' in key:
                        continue
                    params[key] = "string"

            # Extract path parameters only from the path part (not from scheme or port)
            path = parsed.path
            if path:
                path_params = re.findall(r':(\w+)', path)
                for param in path_params:
                    # Skip if it's a number (port number)
                    if param.isdigit():
                        continue
                    # Skip common function names
                    if param in ['encodeURIComponent', 'decodeURIComponent', 'encodeURI', 'decodeURI']:
                        continue
                    params[param] = "path_param"
        except Exception as e:
            # Fallback to simple extraction if URL parsing fails
            pass

        return params

    def _extract_context_info(self, content: str, url: str, match_pos: int) -> Dict:
        """
        Extract method, headers, and body from surrounding context.

        Args:
            content: Full JavaScript content
            url: The matched URL
            match_pos: Position where URL was found

        Returns:
            Dict with 'method', 'headers', 'body'
        """
        result = {
            'method': None,
            'headers': {},
            'body': None
        }

        # Only look FORWARD from the URL match (method comes after URL in code)
        # Look for the end of the fetch/axios call (closing parenthesis)
        # Limit to 300 characters to avoid picking up methods from other calls
        start = match_pos
        end = min(len(content), match_pos + 300)
        context = content[start:end]

        # Find the closing parenthesis of this fetch/axios call
        # Count opening and closing parens to find the matching close
        paren_count = 0
        context_end = len(context)
        for i, char in enumerate(context):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count < 0:  # Found the closing paren of the call
                    context_end = i
                    break

        # Only use context up to the closing paren
        context = context[:context_end]

        try:
            # Extract HTTP method from options object
            # Pattern: { method: 'POST' } or { method: "DELETE" }
            method_match = re.search(r'method:\s*[\'"`](GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)[\'"`]', context, re.IGNORECASE)
            if method_match:
                result['method'] = method_match.group(1).upper()

            # Extract headers
            # Pattern: headers: { 'Content-Type': 'application/json', ... }
            headers_match = re.search(r'headers:\s*\{([^}]+)\}', context, re.DOTALL)
            if headers_match:
                headers_str = headers_match.group(1)
                # Parse header key-value pairs
                header_pairs = re.findall(r'[\'"`]([^\'"`]+)[\'"`]\s*:\s*[\'"`]([^\'"`]+)[\'"`]', headers_str)
                for key, value in header_pairs:
                    result['headers'][key] = value

            # Extract body/data
            # Pattern: body: JSON.stringify({...}) or data: {...}
            body_patterns = [
                r'body:\s*JSON\.stringify\s*\((\{[^}]*\})\)',  # JSON.stringify({...})
                r'body:\s*[\'"`]([^\'"` ]+)[\'"`]',  # body: "string"
                r'data:\s*(\{[^}]+\})',  # data: {...}
            ]

            for pattern in body_patterns:
                body_match = re.search(pattern, context, re.DOTALL)
                if body_match:
                    result['body'] = body_match.group(1)
                    break

        except Exception as e:
            # If context extraction fails, just return empty result
            pass

        return result


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
