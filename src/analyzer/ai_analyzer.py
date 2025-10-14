"""AI-powered JavaScript analysis using OpenAI."""

import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.models import APIEndpoint, HTTPMethod

# Load environment variables
load_dotenv()


class AIJSAnalyzer:
    """AI-powered JavaScript analyzer using OpenAI GPT."""

    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Initialize AI analyzer.

        Args:
            api_key: OpenAI API key (if not provided, reads from OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4-turbo-preview)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        self.enabled = os.getenv('AI_ANALYSIS_ENABLED', 'true').lower() == 'true'

        if not self.api_key:
            print("[!] Warning: OPENAI_API_KEY not found. AI analysis disabled.")
            self.enabled = False
            return

        try:
            self.client = OpenAI(api_key=self.api_key)
            print(f"[+] AI Analyzer initialized with model: {self.model}")
        except Exception as e:
            print(f"[!] Failed to initialize OpenAI client: {e}")
            self.enabled = False

    def analyze_js_code(self, code: str, file_path: str, base_url: str = "") -> List[APIEndpoint]:
        """
        Analyze JavaScript code using AI to extract API endpoints.

        Args:
            code: JavaScript source code
            file_path: Path to the JS file
            base_url: Base URL for relative endpoints

        Returns:
            List of discovered API endpoints
        """
        if not self.enabled:
            return []

        try:
            prompt = self._create_analysis_prompt(code, base_url)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security expert specialized in API endpoint discovery from JavaScript code. Extract all API endpoints, including hidden/shadow APIs. ALWAYS generate PoC (Proof of Concept) Python code for EVERY endpoint you find. The PoC code is MANDATORY."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=int(os.getenv('AI_MAX_TOKENS', '8000')),
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return self._parse_ai_response(result, file_path, base_url)

        except Exception as e:
            print(f"[!] AI analysis error for {file_path}: {e}")
            return []

    def _create_analysis_prompt(self, code: str, base_url: str) -> str:
        """Create analysis prompt for AI."""
        return f"""Analyze the following JavaScript code and extract ALL API endpoints.

JavaScript Code:
```javascript
{code[:8000]}  # Limit code length to avoid token limits
```

Base URL: {base_url if base_url else 'Not provided'}

Instructions:
1. Find ALL API endpoints including:
   - fetch() calls
   - axios requests
   - XMLHttpRequest
   - jQuery $.ajax
   - Hardcoded API URLs
   - Template literals with URLs
   - Dynamic URL construction

2. Identify Shadow APIs (internal/hidden APIs):
   - /internal/*, /admin/*, /debug/*, /test/*
   - /_* (underscore prefix)
   - /api/v0/* (version 0 - usually internal)
   - Endpoints with 'secret', 'hidden', 'private' in path

3. For each endpoint, provide:
   - url: Complete or relative URL
   - method: HTTP method (GET, POST, PUT, DELETE, PATCH)
   - parameters: Query parameters and path parameters
   - is_shadow_api: true if it's a shadow/internal API
   - description: Brief description of what the endpoint does
   - poc_code: Proof of Concept code to test the endpoint (Python using requests library)

CRITICAL: You MUST include poc_code for EVERY endpoint. Do not skip this field.

Return JSON format (MANDATORY fields):
{{
  "endpoints": [
    {{
      "url": "/api/v1/users",
      "method": "GET",
      "parameters": {{}},
      "is_shadow_api": false,
      "description": "Get list of users",
      "poc_code": "import requests\\n\\nurl = 'http://target.com/api/v1/users'\\nresponse = requests.get(url)\\nprint(f'Status: {{response.status_code}}')\\nif response.status_code == 200:\\n    print(f'Response: {{response.json()}}')\\nelse:\\n    print(f'Error: {{response.text}}')"
    }},
    {{
      "url": "/api/internal/admin",
      "method": "POST",
      "parameters": {{"action": "string"}},
      "is_shadow_api": true,
      "description": "Internal admin endpoint",
      "poc_code": "import requests\\n\\nurl = 'http://target.com/api/internal/admin'\\ndata = {{'action': 'test'}}\\nresponse = requests.post(url, json=data)\\nprint(f'Status: {{response.status_code}}')\\nif response.status_code == 200:\\n    print(f'Response: {{response.json()}}')\\nelse:\\n    print(f'Error: {{response.text}}')"
    }}
  ]
}}

Important:
- Include ALL discovered endpoints
- Mark shadow APIs with is_shadow_api: true
- Extract parameters from URL patterns like /api/users/${{id}}
- Handle dynamic URLs and template literals
- Generate realistic PoC code that tests the endpoint
- PoC code should handle authentication if needed (Bearer token, API key, etc.)
- Include error handling and output in PoC code
- Use Python requests library for PoC code
- In PoC code, replace ALL template variables with actual values:
  * Replace ${{id}}, ${{userId}}, :id with numbers like 123, 456
  * Replace ${{name}}, ${{username}} with strings like 'testuser', 'example'
  * NO ${{...}} or :... patterns should remain in the PoC code
"""

    def _parse_ai_response(self, result: Dict, file_path: str, base_url: str) -> List[APIEndpoint]:
        """Parse AI response into APIEndpoint objects."""
        endpoints = []

        for ep in result.get('endpoints', []):
            try:
                # Parse method
                method_str = ep.get('method', 'GET').upper()
                try:
                    method = HTTPMethod[method_str]
                except KeyError:
                    method = HTTPMethod.GET

                # Build complete URL
                url = ep.get('url', '')
                if url.startswith('/') and base_url:
                    url = base_url.rstrip('/') + url

                # Get PoC code or generate default
                poc_code = ep.get('poc_code', None)

                # If no PoC code provided, generate a simple one
                if not poc_code:
                    poc_code = self._generate_default_poc(url, method)

                # Clean template variables
                if poc_code:
                    poc_code = self._clean_template_variables(poc_code)

                # Create endpoint
                endpoint = APIEndpoint(
                    url=url,
                    method=method,
                    parameters=ep.get('parameters', {}),
                    source=f"{file_path} (AI)",
                    response_example=ep.get('description', None),
                    poc_code=poc_code
                )

                endpoints.append(endpoint)

            except Exception as e:
                print(f"[!] Error parsing AI endpoint: {e}")
                continue

        return endpoints

    def enhance_endpoints(self, endpoints: List[APIEndpoint]) -> List[APIEndpoint]:
        """
        Enhance existing endpoints with AI analysis.
        Adds descriptions, identifies shadow APIs, detects parameters.

        Args:
            endpoints: List of endpoints to enhance

        Returns:
            Enhanced list of endpoints
        """
        if not self.enabled or not endpoints:
            return endpoints

        try:
            # Create summary of endpoints
            endpoint_summary = "\n".join([
                f"{ep.method} {ep.url}"
                for ep in endpoints[:20]  # Limit to first 20 to avoid token limits
            ])

            prompt = f"""Analyze these API endpoints and identify:
1. Which are shadow/internal APIs (return boolean for each)
2. Potential security risks
3. Missing parameters that might exist

Endpoints:
{endpoint_summary}

Return JSON:
{{
  "analysis": [
    {{
      "url": "/api/users",
      "is_shadow_api": false,
      "risk_level": "low|medium|high",
      "potential_parameters": ["id", "page", "limit"],
      "notes": "Brief security notes"
    }}
  ]
}}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing API endpoints."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Enhance endpoints with AI insights
            analysis_map = {a['url']: a for a in result.get('analysis', [])}

            for endpoint in endpoints:
                if endpoint.url in analysis_map:
                    insight = analysis_map[endpoint.url]

                    # Add potential parameters
                    if 'potential_parameters' in insight:
                        for param in insight['potential_parameters']:
                            if param not in endpoint.parameters:
                                endpoint.parameters[param] = "inferred_by_ai"

                    # Add notes to response_example
                    if insight.get('notes'):
                        endpoint.response_example = insight['notes']

            return endpoints

        except Exception as e:
            print(f"[!] AI enhancement error: {e}")
            return endpoints

    def generate_vulnerability_poc(self, vulnerabilities: List) -> List:
        """
        Generate PoC code for discovered vulnerabilities.

        Args:
            vulnerabilities: List of Vulnerability objects

        Returns:
            Enhanced list of vulnerabilities with PoC code
        """
        if not self.enabled or not vulnerabilities:
            return vulnerabilities

        try:
            # Process vulnerabilities in batches to avoid token limits
            for vuln in vulnerabilities[:10]:  # Limit to first 10 to manage costs
                prompt = f"""Generate a Proof of Concept (PoC) code to demonstrate this security vulnerability.

Vulnerability Details:
- Type: {vuln.type}
- Severity: {vuln.level}
- Endpoint: {vuln.method} {vuln.endpoint}
- Description: {vuln.description}
- Evidence: {vuln.evidence}

Requirements:
1. Write Python code using the requests library
2. Include clear comments explaining each step
3. Add error handling and output formatting
4. Show how to exploit the vulnerability safely (for testing purposes only)
5. Include authentication if needed
6. Demonstrate the vulnerability clearly with expected vs actual behavior
7. Replace ALL template variables with actual example values:
   - Replace ${{id}}, ${{userId}}, ${{postId}} etc. with actual numbers (e.g., 123, 456)
   - Replace :id, :userId, :postId in URLs with actual numbers
   - Replace ${{name}}, ${{username}} with actual strings (e.g., 'testuser', 'example')
   - NO template variables should remain in the code

IMPORTANT:
- This is for defensive security testing only. Add appropriate warnings.
- Use actual concrete values instead of template variables

Return ONLY the Python code, no explanation needed."""

                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a security expert creating PoC code for defensive penetration testing. Generate safe, educational PoC code."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.2,
                        max_tokens=1500
                    )

                    poc_code = response.choices[0].message.content.strip()

                    # Remove markdown code blocks if present
                    if poc_code.startswith('```python'):
                        poc_code = poc_code.replace('```python', '', 1)
                    if poc_code.startswith('```'):
                        poc_code = poc_code.replace('```', '', 1)
                    if poc_code.endswith('```'):
                        poc_code = poc_code.rsplit('```', 1)[0]

                    # Replace template variables with example values
                    poc_code = self._clean_template_variables(poc_code)

                    vuln.poc_code = poc_code.strip()
                    print(f"[+] Generated PoC for {vuln.type} vulnerability")

                except Exception as e:
                    print(f"[!] Failed to generate PoC for {vuln.type}: {e}")
                    continue

            return vulnerabilities

        except Exception as e:
            print(f"[!] Vulnerability PoC generation error: {e}")
            return vulnerabilities

    @staticmethod
    def _generate_default_poc(url: str, method: str) -> str:
        """Generate a default PoC code if AI doesn't provide one."""
        method_lower = method.lower() if hasattr(method, 'lower') else str(method).lower()

        if method_lower in ['post', 'put', 'patch']:
            return f"""import requests

url = '{url}'
data = {{'key': 'value'}}
headers = {{'Content-Type': 'application/json'}}

response = requests.{method_lower}(url, json=data, headers=headers)
print(f'Status: {{response.status_code}}')
if response.status_code == 200:
    print(f'Response: {{response.json()}}')
else:
    print(f'Error: {{response.text}}')
"""
        else:
            return f"""import requests

url = '{url}'
response = requests.{method_lower}(url)
print(f'Status: {{response.status_code}}')
if response.status_code == 200:
    try:
        print(f'Response: {{response.json()}}')
    except:
        print(f'Response: {{response.text}}')
else:
    print(f'Error: {{response.text}}')
"""

    def _clean_template_variables(self, code: str) -> str:
        """
        Clean template variables from generated PoC code.
        Replaces ${variable}, :variable patterns with example values.
        """
        import re

        # Replace JavaScript template literals: ${variable} -> 123
        # Common patterns
        replacements = {
            r'\$\{id\}': '123',
            r'\$\{userId\}': '123',
            r'\$\{postId\}': '456',
            r'\$\{productId\}': '789',
            r'\$\{orderId\}': '101',
            r'\$\{commentId\}': '202',
            r'\$\{name\}': 'example',
            r'\$\{username\}': 'testuser',
            r'\$\{email\}': 'test@example.com',
            r'\$\{token\}': 'sample_token_123',
            r'\$\{key\}': 'sample_key',
            r'\$\{value\}': 'sample_value',
        }

        for pattern, replacement in replacements.items():
            code = re.sub(pattern, replacement, code)

        # Catch-all for any remaining ${...} patterns
        code = re.sub(r'\$\{(\w+)\}', r'123', code)

        # Replace URL parameter templates: :id -> 123
        code = re.sub(r':id\b', '123', code)
        code = re.sub(r':userId\b', '123', code)
        code = re.sub(r':postId\b', '456', code)
        code = re.sub(r':productId\b', '789', code)
        code = re.sub(r':(\w+)Id\b', r'123', code)  # Any :somethingId
        code = re.sub(r':name\b', 'example', code)
        code = re.sub(r':(\w+)\b', 'value', code)  # Catch-all for :anything

        return code
