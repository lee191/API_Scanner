"""Generate curl commands for API endpoints."""

import json
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, quote
from src.utils.models import APIEndpoint, HTTPMethod


class CurlGenerator:
    """Generate curl commands for Windows (PowerShell and CMD)."""

    @staticmethod
    def _generate_curl_with_ai(endpoint: APIEndpoint, include_auth: bool = False, 
                               auth_token: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Use AI to generate complete curl commands for all formats.
        
        Args:
            endpoint: API endpoint information
            include_auth: Whether to include authentication
            auth_token: Optional authentication token
            
        Returns:
            Dict with curl commands or None if AI fails
        """
        try:
            from src.analyzer.ai_analyzer import AIJSAnalyzer
            ai_analyzer = AIJSAnalyzer()
            
            if not ai_analyzer.enabled:
                return None
            
            # Prepare endpoint information
            endpoint_data = {
                "url": endpoint.url,
                "method": endpoint.method.upper(),
                "headers": endpoint.headers or {},
                "parameters": endpoint.parameters or {},
                "body": endpoint.body_example,
                "source": endpoint.source
            }
            
            if include_auth and auth_token:
                endpoint_data["headers"]["Authorization"] = f"Bearer {auth_token}"
            
            # Extract base URL from endpoint URL for examples
            parsed_url = endpoint.url
            # Try to extract protocol and host
            if parsed_url.startswith(('http://', 'https://')):
                # Extract base URL (protocol + host + port)
                parts = parsed_url.split('/')
                base_url = f"{parts[0]}//{parts[2]}" if len(parts) > 2 else parsed_url
            else:
                # Default to discovered URL pattern
                base_url = "http://localhost:5000"
                if parsed_url.startswith(':'):
                    port = parsed_url[1:].split('/')[0]
                    if port.isdigit():
                        base_url = f"http://localhost:{port}"
            
            # AI prompt for complete curl generation
            prompt = f"""You MUST respond with ONLY a valid JSON object. No explanations, no markdown, just JSON.

API Endpoint:
{json.dumps(endpoint_data, indent=2)}

Task: Generate curl commands for Windows (PowerShell, CMD, Bash/WSL)

Rules:
1. Fix malformed URLs - ensure proper protocol and host:
   - `:5000/path` → `http://localhost:5000/path`
   - `:port/path` → `http://localhost:port/path`
   - `/path` → Use original base URL + `/path`
   - Keep existing protocol and host if URL is well-formed

2. Replace path placeholders with realistic example values:
   - `:id` / `{{id}}` → 123
   - `:userId` / `{{userId}}` → 123
   - `:postId` / `{{postId}}` → 456
   - `:param` → example_value (do NOT replace with localhost:5000)
   
3. Preserve the original base URL (protocol + host + port) from the endpoint
4. Include all query parameters if present
5. Add helpful instruction comment explaining what values to replace

Response format (ONLY JSON, NO OTHER TEXT):
{{
  "powershell": "# Replace 123 with actual user ID\\nInvoke-WebRequest -Uri \\"{base_url}/api/users/123\\" `\\n    -Method GET `\\n    -UseBasicParsing",
  "cmd": "REM Replace 123 with actual user ID\\ncurl.exe -X GET \\"{base_url}/api/users/123\\"",
  "bash": "# Replace 123 with actual user ID\\ncurl -X GET '{base_url}/api/users/123'",
  "url": "{base_url}/api/users/123",
  "method": "GET",
  "instruction": "Replace 123 with actual user ID"
}}

CRITICAL: Use the actual base URL from the endpoint ({base_url}), NOT a hardcoded localhost:5000.
IMPORTANT: Return ONLY the JSON object. No markdown code blocks, no explanations."""
            
            response = ai_analyzer.client.chat.completions.create(
                model=ai_analyzer.model,
                messages=[
                    {"role": "system", "content": "You are a JSON API. You ONLY output valid JSON. Never use markdown code blocks. Never add explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            content = content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(content)
                
                # Validate required fields
                if all(key in result for key in ['powershell', 'cmd', 'bash', 'url', 'method']):
                    return result
                else:
                    print(f"[!] AI response missing required fields: {list(result.keys())}")
                    return None
            except json.JSONDecodeError as je:
                print(f"[!] JSON parsing failed: {je}")
                print(f"[!] AI Response: {content[:200]}...")
                return None
                
        except Exception as e:
            print(f"[!] AI curl generation failed: {e}, using basic generation")
            return None
    
    @staticmethod
    def _basic_url_cleanup(url: str) -> str:
        """Basic URL cleanup without AI."""
        # Fix URL starting with colon (priority: handle first!)
        if url.startswith(':'):
            parts = url[1:].split('/', 1)
            first_part = parts[0]
            path = '/' + parts[1] if len(parts) > 1 else '/'
            
            # Check if it's a port number or placeholder
            if first_part.isdigit():
                # It's a port: :5000/api/path -> http://localhost:5000/api/path
                url = f'http://localhost:{first_part}{path}'
            else:
                # It's a placeholder: :param/api/path -> http://localhost:5000/api/path
                url = f'http://localhost:5000{path}'
        
        # Replace common placeholders with example values (in path/query only)
        url = re.sub(r':id\b', '1', url)
        url = re.sub(r'\{id\}', '1', url)
        url = re.sub(r':userId\b', '123', url)
        url = re.sub(r'\{userId\}', '123', url)
        url = re.sub(r':postId\b', '1', url)
        url = re.sub(r'\{postId\}', '1', url)
        url = re.sub(r':([a-zA-Z_][a-zA-Z0-9_]*)', r'example_\1', url)
        url = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', r'example_\1', url)
        
        # Ensure protocol
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        return url

    @staticmethod
    def generate_curl(endpoint: APIEndpoint, include_auth: bool = False, 
                     auth_token: Optional[str] = None, use_ai: bool = True) -> Dict[str, str]:
        """
        Generate curl commands for PowerShell, CMD, and Bash.
        
        Args:
            endpoint: API endpoint information
            include_auth: Whether to include authentication header
            auth_token: Optional authentication token
            use_ai: Use AI to generate complete curl commands (default: True)
            
        Returns:
            Dictionary with 'powershell', 'cmd', 'bash' curl commands
        """
        # Try AI-powered complete curl generation first
        if use_ai:
            ai_result = CurlGenerator._generate_curl_with_ai(endpoint, include_auth, auth_token)
            if ai_result:
                print("[+] AI successfully generated curl commands")
                return ai_result
            print("[!] AI generation failed, falling back to basic generation")
        
        # Fallback: Basic generation with URL cleanup
        url = endpoint.url
        method = endpoint.method.upper()
        headers = endpoint.headers.copy() if endpoint.headers else {}
        params = endpoint.parameters.copy() if endpoint.parameters else {}
        body = endpoint.body_example
        
        # Clean URL with basic cleanup
        url = CurlGenerator._basic_url_cleanup(url)
        
        # Add authentication if specified
        if include_auth and auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        # Generate PowerShell curl (Invoke-WebRequest style)
        powershell_cmd = CurlGenerator._generate_powershell(
            url, method, headers, params, body
        )
        
        # Generate CMD curl (traditional curl.exe style)
        cmd_curl = CurlGenerator._generate_cmd(
            url, method, headers, params, body
        )
        
        # Generate bash-style curl (for WSL or Git Bash)
        bash_curl = CurlGenerator._generate_bash(
            url, method, headers, params, body
        )
        
        return {
            'powershell': powershell_cmd,
            'cmd': cmd_curl,
            'bash': bash_curl,
            'url': url,
            'method': method,
            'instruction': ''
        }
    
    @staticmethod
    def _generate_powershell(url: str, method: str, headers: Dict[str, str],
                            params: Dict[str, str], body: Optional[str]) -> str:
        """Generate PowerShell Invoke-WebRequest command."""
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            # Check if URL starts with :port (malformed - missing host)
            if url.startswith(':'):
                # Extract port and path
                parts = url[1:].split('/', 1)
                port = parts[0]
                path = '/' + parts[1] if len(parts) > 1 else '/'
                url = f'http://localhost:{port}{path}'
            else:
                url = 'http://' + url
        
        # Add query parameters to URL
        if params:
            # Check if URL already has query params
            separator = '&' if '?' in url else '?'
            param_str = urlencode(params)
            url = f"{url}{separator}{param_str}"
        
        cmd_parts = [f'Invoke-WebRequest -Uri "{url}"']
        cmd_parts.append(f'-Method {method}')
        
        # Add headers
        if headers:
            header_dict = ', '.join([f"'{k}'='{v}'" for k, v in headers.items()])
            cmd_parts.append(f'-Headers @{{{header_dict}}}')
        
        # Add body
        if body and method in ['POST', 'PUT', 'PATCH']:
            # Escape double quotes in JSON
            escaped_body = body.replace('"', '`"')
            cmd_parts.append(f'-Body "{escaped_body}"')
            if 'Content-Type' not in headers:
                cmd_parts.append('-ContentType "application/json"')
        
        # Add common options
        cmd_parts.append('-UseBasicParsing')
        
        return ' `\n    '.join(cmd_parts)
    
    @staticmethod
    def _generate_cmd(url: str, method: str, headers: Dict[str, str],
                     params: Dict[str, str], body: Optional[str]) -> str:
        """Generate CMD curl.exe command."""
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            if url.startswith(':'):
                # Extract port and path
                parts = url[1:].split('/', 1)
                port = parts[0]
                path = '/' + parts[1] if len(parts) > 1 else '/'
                url = f'http://localhost:{port}{path}'
            else:
                url = 'http://' + url
        
        # Add query parameters to URL
        if params:
            separator = '&' if '?' in url else '?'
            param_str = urlencode(params)
            url = f"{url}{separator}{param_str}"
        
        cmd_parts = ['curl']
        cmd_parts.append(f'-X {method}')
        cmd_parts.append(f'"{url}"')
        
        # Add headers
        for key, value in headers.items():
            # Escape double quotes for CMD
            escaped_value = value.replace('"', '\\"')
            cmd_parts.append(f'-H "^{key}: {escaped_value}"')
        
        # Add body
        if body and method in ['POST', 'PUT', 'PATCH']:
            # Escape for CMD (complex, use file or simple approach)
            escaped_body = body.replace('"', '\\"')
            cmd_parts.append(f'-d "{escaped_body}"')
            if not any('Content-Type' in h for h in headers):
                cmd_parts.append('-H "Content-Type: application/json"')
        
        # Add common options
        cmd_parts.append('-k')  # Insecure (ignore SSL)
        cmd_parts.append('-i')  # Include response headers
        
        return ' ^\n    '.join(cmd_parts)
    
    @staticmethod
    def _generate_bash(url: str, method: str, headers: Dict[str, str],
                      params: Dict[str, str], body: Optional[str]) -> str:
        """Generate bash-style curl command (for WSL, Git Bash)."""
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            if url.startswith(':'):
                # Extract port and path
                parts = url[1:].split('/', 1)
                port = parts[0]
                path = '/' + parts[1] if len(parts) > 1 else '/'
                url = f'http://localhost:{port}{path}'
            else:
                url = 'http://' + url
        
        # Add query parameters to URL
        if params:
            separator = '&' if '?' in url else '?'
            param_str = urlencode(params)
            url = f"{url}{separator}{param_str}"
        
        cmd_parts = ['curl']
        cmd_parts.append(f'-X {method}')
        cmd_parts.append(f"'{url}'")
        
        # Add headers
        for key, value in headers.items():
            cmd_parts.append(f"-H '{key}: {value}'")
        
        # Add body
        if body and method in ['POST', 'PUT', 'PATCH']:
            # Single quotes for bash
            escaped_body = body.replace("'", "'\\''")
            cmd_parts.append(f"-d '{escaped_body}'")
            if not any('Content-Type' in h for h in headers):
                cmd_parts.append("-H 'Content-Type: application/json'")
        
        # Add common options
        cmd_parts.append('-k')  # Insecure (ignore SSL)
        cmd_parts.append('-i')  # Include response headers
        
        return ' \\\n    '.join(cmd_parts)
    
    @staticmethod
    def generate_examples() -> Dict[str, Dict[str, str]]:
        """Generate example curl commands for common scenarios."""
        examples = {}
        
        # GET request example
        get_endpoint = APIEndpoint(
            url="http://api.example.com/users",
            method=HTTPMethod.GET,
            parameters={"page": "1", "limit": "10"}
        )
        examples['get_request'] = CurlGenerator.generate_curl(get_endpoint)
        
        # POST request example
        post_endpoint = APIEndpoint(
            url="http://api.example.com/users",
            method=HTTPMethod.POST,
            headers={"Content-Type": "application/json"},
            body_example='{"name": "John Doe", "email": "john@example.com"}'
        )
        examples['post_request'] = CurlGenerator.generate_curl(post_endpoint)
        
        # Authenticated request example
        auth_endpoint = APIEndpoint(
            url="http://api.example.com/profile",
            method=HTTPMethod.GET
        )
        examples['auth_request'] = CurlGenerator.generate_curl(
            auth_endpoint, 
            include_auth=True, 
            auth_token="your_token_here"
        )
        
        return examples
    
    @staticmethod
    def generate_postman_collection(endpoints: list, collection_name: str = "API Collection") -> dict:
        """
        Generate Postman collection from endpoints.
        
        Args:
            endpoints: List of APIEndpoint objects
            collection_name: Name for the Postman collection
            
        Returns:
            Postman collection JSON
        """
        collection = {
            "info": {
                "name": collection_name,
                "description": "Generated by Shadow API Scanner",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        for endpoint in endpoints:
            url_parts = endpoint.url.split('?')
            base_url = url_parts[0]
            
            # Parse query parameters
            query_params = []
            if endpoint.parameters:
                for key, value in endpoint.parameters.items():
                    query_params.append({
                        "key": key,
                        "value": value
                    })
            
            # Build headers
            header_list = []
            if endpoint.headers:
                for key, value in endpoint.headers.items():
                    header_list.append({
                        "key": key,
                        "value": value
                    })
            
            # Build request item
            item = {
                "name": f"{endpoint.method} {base_url}",
                "request": {
                    "method": endpoint.method,
                    "header": header_list,
                    "url": {
                        "raw": endpoint.url,
                        "protocol": "http" if endpoint.url.startswith("http://") else "https",
                        "host": [base_url.split('/')[2]],
                        "path": base_url.split('/')[3:],
                        "query": query_params
                    }
                }
            }
            
            # Add body if applicable
            if endpoint.body_example and endpoint.method in ['POST', 'PUT', 'PATCH']:
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": endpoint.body_example,
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            collection["item"].append(item)
        
        return collection


def main():
    """Example usage."""
    # Example 1: Simple GET request
    endpoint = APIEndpoint(
        url="http://localhost:5000/api/v1/users",
        method=HTTPMethod.GET,
        parameters={"page": "1", "limit": "10"}
    )
    
    curl_commands = CurlGenerator.generate_curl(endpoint)
    
    print("=" * 80)
    print("PowerShell Command:")
    print("=" * 80)
    print(curl_commands['powershell'])
    
    print("\n" + "=" * 80)
    print("CMD Command:")
    print("=" * 80)
    print(curl_commands['cmd'])
    
    print("\n" + "=" * 80)
    print("Bash Command (WSL/Git Bash):")
    print("=" * 80)
    print(curl_commands['bash'])


if __name__ == "__main__":
    main()
