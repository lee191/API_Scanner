"""cURL command generator for endpoint validation."""

import json
import shlex
from typing import Dict, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from src.utils.models import APIEndpoint, HTTPMethod


class CurlGenerator:
    """Generate cURL commands for API endpoint validation."""

    # Example values for different parameter types
    EXAMPLE_VALUES = {
        # Common parameter names
        'id': '123',
        'user_id': '1',
        'userid': '1',
        'post_id': '1',
        'postid': '1',
        'product_id': '1',
        'productid': '1',
        'order_id': '1',
        'orderid': '1',
        'item_id': '1',
        'itemid': '1',

        # Search and filter
        'search': 'test',
        'query': 'example',
        'q': 'search',
        'keyword': 'test',
        'filter': 'active',
        'category': 'general',
        'tag': 'sample',
        'tags': 'tag1,tag2',

        # Pagination
        'page': '1',
        'limit': '10',
        'offset': '0',
        'size': '10',
        'per_page': '10',
        'perpage': '10',

        # Sorting
        'sort': 'asc',
        'order': 'desc',
        'orderby': 'created_at',
        'sortby': 'name',

        # User info
        'name': 'john',
        'username': 'johndoe',
        'email': 'user@example.com',
        'password': 'password123',

        # Status
        'status': 'active',
        'state': 'pending',
        'type': 'default',

        # Date/Time
        'date': '2024-01-01',
        'from': '2024-01-01',
        'to': '2024-12-31',
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',

        # Boolean
        'active': 'true',
        'enabled': 'true',
        'public': 'true',
        'published': 'true',

        # Auth
        'token': 'sample_token_123',
        'api_key': 'api_key_123',
        'apikey': 'api_key_123',
        'access_token': 'access_token_123',
    }

    @staticmethod
    def _generate_example_value(param_name: str, param_type: str) -> str:
        """
        Generate example value for a parameter based on its name and type.

        Args:
            param_name: Name of the parameter
            param_type: Type of the parameter (string, path_param, etc.)

        Returns:
            Example value string
        """
        # Normalize parameter name for matching
        normalized_name = param_name.lower().replace('-', '_')

        # Check if we have a predefined example for this parameter name
        if normalized_name in CurlGenerator.EXAMPLE_VALUES:
            return CurlGenerator.EXAMPLE_VALUES[normalized_name]

        # For path parameters, use numeric IDs
        if param_type == 'path_param':
            # Check if it's some kind of ID
            if 'id' in normalized_name:
                return '123'
            # Otherwise use the parameter name as a placeholder
            return f'{param_name}_value'

        # Pattern-based matching for common cases
        if 'email' in normalized_name:
            return 'user@example.com'
        elif 'phone' in normalized_name or 'mobile' in normalized_name:
            return '1234567890'
        elif 'url' in normalized_name or 'link' in normalized_name:
            return 'https://example.com'
        elif 'count' in normalized_name or 'number' in normalized_name or 'num' in normalized_name:
            return '10'
        elif 'price' in normalized_name or 'amount' in normalized_name:
            return '99.99'
        elif 'description' in normalized_name or 'desc' in normalized_name:
            return 'sample description'
        elif 'title' in normalized_name:
            return 'Sample Title'
        elif 'message' in normalized_name or 'msg' in normalized_name:
            return 'Sample message'
        elif 'code' in normalized_name:
            return 'ABC123'
        elif 'color' in normalized_name:
            return 'blue'
        elif 'lang' in normalized_name or 'language' in normalized_name:
            return 'en'
        elif 'country' in normalized_name:
            return 'US'
        elif 'city' in normalized_name:
            return 'New York'
        elif 'address' in normalized_name:
            return '123 Main St'
        elif 'zip' in normalized_name or 'postal' in normalized_name:
            return '12345'

        # Default: use parameter name as hint
        return f'example_{normalized_name}'

    @staticmethod
    def generate(endpoint: APIEndpoint, verbose: bool = False, include_response: bool = False) -> str:
        """
        Generate a cURL command for the given endpoint.

        Args:
            endpoint: APIEndpoint object with URL, method, parameters, headers, body
            verbose: Include -v flag for verbose output
            include_response: Include -i flag to show response headers

        Returns:
            cURL command string ready to execute
        """
        parts = ["curl"]

        # Add flags
        if verbose:
            parts.append("-v")
        if include_response:
            parts.append("-i")

        # Add HTTP method
        method = endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method)
        parts.extend(["-X", method])

        # Build URL with query parameters for GET/DELETE requests
        url = CurlGenerator._build_url(endpoint.url, endpoint.parameters, method)

        # Add headers
        headers_added = False
        if endpoint.headers:
            for key, value in endpoint.headers.items():
                parts.extend(["-H", f"{key}: {value}"])
                headers_added = True

        # Add body data for POST/PUT/PATCH requests
        if method in ["POST", "PUT", "PATCH"]:
            if endpoint.body_example:
                # Try to parse as JSON first
                try:
                    # Validate JSON and format it
                    json_data = json.loads(endpoint.body_example)
                    if not headers_added or not any("content-type" in h.lower() for h in endpoint.headers.keys()):
                        parts.extend(["-H", "Content-Type: application/json"])
                    parts.extend(["-d", json.dumps(json_data)])
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, treat as raw body
                    parts.extend(["-d", endpoint.body_example])
            elif endpoint.parameters and method != "GET":
                # Use parameters as form data with example values for non-GET requests
                for key, value_type in endpoint.parameters.items():
                    # Skip path parameters (they're already in the URL)
                    if f':{key}' in url:
                        continue
                    example_value = CurlGenerator._generate_example_value(key, value_type)
                    parts.extend(["-d", f"{key}={example_value}"])

        # Add URL (must be last)
        parts.append(url)

        return CurlGenerator._format_command(parts)

    @staticmethod
    def _build_url(base_url: str, parameters: Optional[Dict[str, str]], method: str) -> str:
        """
        Build complete URL with query parameters and example values.

        For GET/DELETE requests, append parameters as query string.
        For other methods, parameters are typically sent in body.
        """
        if not parameters or method not in ["GET", "DELETE", "HEAD", "OPTIONS"]:
            # Still need to replace path parameters in URL
            if parameters:
                url = base_url
                for key, value_type in parameters.items():
                    # Replace path parameters like /users/:id -> /users/123
                    if f':{key}' in url:
                        example_value = CurlGenerator._generate_example_value(key, value_type)
                        url = url.replace(f':{key}', example_value)
                return url
            return base_url

        # Parse existing URL
        parsed = urlparse(base_url)
        path = parsed.path

        # Replace path parameters in URL
        path_params_to_remove = []
        for key, value_type in parameters.items():
            if f':{key}' in path:
                example_value = CurlGenerator._generate_example_value(key, value_type)
                path = path.replace(f':{key}', example_value)
                path_params_to_remove.append(key)

        # Merge existing query params with new parameters (excluding path params)
        existing_params = parse_qs(parsed.query)
        merged_params = {**existing_params}

        # Add new query parameters with example values
        for key, value_type in parameters.items():
            if key not in path_params_to_remove and key not in merged_params:
                example_value = CurlGenerator._generate_example_value(key, value_type)
                merged_params[key] = [example_value]

        # Flatten single-value lists back to strings
        query_params = {}
        for key, values in merged_params.items():
            query_params[key] = values[0] if len(values) == 1 else values

        # Build new query string
        new_query = urlencode(query_params, doseq=True) if query_params else ''

        # Reconstruct URL with updated path
        new_parsed = parsed._replace(path=path, query=new_query)
        return urlunparse(new_parsed)

    @staticmethod
    def _format_command(parts: list) -> str:
        """
        Format cURL command parts into a readable string.

        Uses shlex.quote for proper shell escaping.
        For commands with multiple parts, format with line continuations.
        """
        # Quote each part properly for shell
        quoted_parts = []
        for i, part in enumerate(parts):
            # Don't quote flags
            if part.startswith("-") and not part.startswith("-d") and not part.startswith("-H") and not part.startswith("-X"):
                quoted_parts.append(part)
            # For -d, -H, -X flags, quote the next part
            elif i > 0 and parts[i-1] in ["-d", "-H", "-X"]:
                quoted_parts.append(shlex.quote(part))
            # Quote URL (last part)
            elif i == len(parts) - 1:
                quoted_parts.append(shlex.quote(part))
            else:
                quoted_parts.append(part)

        # If command is simple (curl -X METHOD url), return single line
        if len(quoted_parts) <= 4:
            return " ".join(quoted_parts)

        # For complex commands, format with line continuations
        result = [quoted_parts[0]]  # Start with 'curl'

        for i in range(1, len(quoted_parts)):
            part = quoted_parts[i]
            # Add line continuation for better readability
            if part.startswith("-"):
                result.append(" \\\n  " + part)
            else:
                result.append(" " + part)

        return "".join(result)

    @staticmethod
    def generate_batch(endpoints: list, output_file: Optional[str] = None) -> str:
        """
        Generate cURL commands for multiple endpoints.

        Args:
            endpoints: List of APIEndpoint objects
            output_file: Optional file path to write commands to

        Returns:
            String containing all cURL commands, separated by newlines
        """
        commands = []

        for i, endpoint in enumerate(endpoints, 1):
            # Add comment with endpoint info
            method = endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method)
            commands.append(f"\n# Endpoint {i}: {method} {endpoint.url}")
            commands.append(f"# Source: {endpoint.source}")

            # Generate curl command
            curl_cmd = CurlGenerator.generate(endpoint)
            commands.append(curl_cmd)
            commands.append("")  # Empty line for separation

        result = "\n".join(commands)

        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n\n")
                f.write("# cURL commands for API endpoint validation\n")
                f.write(f"# Generated for {len(endpoints)} endpoints\n\n")
                f.write(result)
            print(f"[+] cURL commands written to: {output_file}")

        return result

    @staticmethod
    def generate_validation_script(endpoints: list, output_file: str = "validate_endpoints.sh") -> str:
        """
        Generate a bash script that tests all endpoints and reports results.

        Args:
            endpoints: List of APIEndpoint objects
            output_file: Output file path for the script

        Returns:
            Path to the generated script
        """
        script_lines = [
            "#!/bin/bash",
            "",
            "# API Endpoint Validation Script",
            f"# Total endpoints: {len(endpoints)}",
            "",
            "echo '=== API Endpoint Validation ==='",
            "echo ''",
            "",
            "PASS=0",
            "FAIL=0",
            "TOTAL=0",
            ""
        ]

        for i, endpoint in enumerate(endpoints, 1):
            method = endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method)

            script_lines.append(f"# Test {i}: {method} {endpoint.url}")
            script_lines.append(f"echo 'Testing endpoint {i}/{len(endpoints)}: {method} {endpoint.url}'")

            # Generate curl command with status code capture
            curl_cmd = CurlGenerator.generate(endpoint, include_response=False)

            # Add HTTP status code check
            script_lines.append(f"HTTP_CODE=$(curl -s -o /dev/null -w '%{{http_code}}' {curl_cmd.replace('curl ', '').strip()})")
            script_lines.append(f"TOTAL=$((TOTAL + 1))")
            script_lines.append("")
            script_lines.append("if [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 400 ]; then")
            script_lines.append(f"  echo '  ✓ PASS (HTTP $HTTP_CODE)'")
            script_lines.append("  PASS=$((PASS + 1))")
            script_lines.append("else")
            script_lines.append(f"  echo '  ✗ FAIL (HTTP $HTTP_CODE)'")
            script_lines.append("  FAIL=$((FAIL + 1))")
            script_lines.append("fi")
            script_lines.append("echo ''")
            script_lines.append("")

        # Add summary
        script_lines.extend([
            "echo '=== Validation Summary ==='",
            "echo \"Total: $TOTAL\"",
            "echo \"Passed: $PASS\"",
            "echo \"Failed: $FAIL\"",
            "",
            "if [ $FAIL -eq 0 ]; then",
            "  echo '✓ All endpoints validated successfully!'",
            "  exit 0",
            "else",
            "  echo '✗ Some endpoints failed validation'",
            "  exit 1",
            "fi"
        ])

        # Write script to file
        with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write("\n".join(script_lines))

        print(f"[+] Validation script created: {output_file}")
        print(f"    Run with: bash {output_file}")

        return output_file
