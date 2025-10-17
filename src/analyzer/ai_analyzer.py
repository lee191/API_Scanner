"""AI-powered endpoint inference and verification using OpenAI GPT models."""

import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.models import APIEndpoint, HTTPMethod

# Load environment variables
load_dotenv()


class AIAnalyzer:
    """
    AI-powered analyzer for intelligent endpoint inference and verification.

    Features:
    - JavaScript code analysis to infer hidden endpoints
    - Smart endpoint verification with HTTP requests
    - Pattern recognition for API structures
    - Confidence scoring for inferred endpoints
    """

    def __init__(self, api_key: Optional[str] = None, prompts_dir: Optional[str] = None, language: str = 'ko'):
        """
        Initialize AI analyzer with OpenAI API key.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY from .env)
            prompts_dir: Directory containing prompt txt files (defaults to src/prompts)
            language: Language for prompts ('ko' for Korean, 'en' for English, default: 'ko')
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file.")

        self.client = OpenAI(api_key=self.api_key)
        # Get AI model from environment variable or use default
        self.model = os.getenv('AI_MODEL', 'gpt-4o')  # Using GPT-4o for better performance

        # Get language from environment variable or parameter
        env_language = os.getenv('AI_PROMPT_LANGUAGE', 'ko')
        self.language = language if language else env_language

        # Load prompts from files
        if prompts_dir is None:
            # Default to src/prompts relative to this file
            current_dir = Path(__file__).parent.parent
            prompts_dir = current_dir / 'prompts'
        else:
            prompts_dir = Path(prompts_dir)

        # Add language subdirectory
        self.prompts_dir = prompts_dir / language

        # Fallback to English if language directory doesn't exist
        if not self.prompts_dir.exists():
            print(f"[!] Prompts for '{language}' not found, falling back to 'en'")
            self.prompts_dir = prompts_dir / 'en'

        # Final fallback to parent directory
        if not self.prompts_dir.exists():
            print(f"[!] Language-specific prompts not found, using default directory")
            self.prompts_dir = prompts_dir

        self.prompts = self._load_all_prompts()

    def _load_prompt(self, filename: str) -> Optional[str]:
        """
        Load a prompt from a text file.

        Args:
            filename: Name of the prompt file (e.g., 'js_analysis.txt')

        Returns:
            Prompt text or None if file not found
        """
        try:
            filepath = self.prompts_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"[!] Prompt file not found: {filepath}")
                return None
        except Exception as e:
            print(f"[!] Error loading prompt {filename}: {e}")
            return None

    def _load_all_prompts(self) -> Dict[str, str]:
        """
        Load all prompt files.

        Returns:
            Dictionary of prompt_name -> prompt_text
        """
        prompts = {}
        prompt_files = {
            'js_analysis': 'js_analysis.txt',
            'endpoint_verification': 'endpoint_verification.txt',
        }

        for key, filename in prompt_files.items():
            prompt = self._load_prompt(filename)
            if prompt:
                prompts[key] = prompt
            else:
                # Fallback to hardcoded prompts
                print(f"[!] Using fallback prompt for {key}")
                prompts[key] = self._get_fallback_prompt(key)

        return prompts

    def _get_fallback_prompt(self, prompt_type: str) -> str:
        """
        Get fallback hardcoded prompt if file loading fails.

        Args:
            prompt_type: Type of prompt needed

        Returns:
            Fallback prompt text
        """
        fallbacks = {
            'js_analysis': """Analyze this JavaScript code and infer API endpoints.

JavaScript code:
{js_content}

Base URL: {base_url}

Return JSON with inferred endpoints, their methods, confidence scores, and reasoning.""",
            'endpoint_verification': """Plan verification strategy for this endpoint:
URL: {url}
Method: {method}

Return JSON with test requests and expected responses.""",
        }
        return fallbacks.get(prompt_type, "Analyze this input.")

    def infer_endpoints_from_js(self, js_content: str, base_url: str, source: str = "ai_inference") -> List[Dict]:
        """
        Analyze JavaScript code to infer hidden API endpoints.

        Args:
            js_content: JavaScript code content
            base_url: Base URL of the target application
            source: Source identifier for tracking

        Returns:
            List of inferred endpoint dictionaries with confidence scores
        """
        # Truncate very large JS files to avoid token limits
        max_length = 80000
        if len(js_content) > max_length:
            print(f"[*] JS content truncated from {len(js_content)} to {max_length} chars")
            js_content = js_content[:max_length] + "\n... (truncated)"

        # Build user prompt with template variables
        user_prompt = self.prompts['js_analysis'].format(
            js_content=js_content,
            base_url=base_url
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            result = json.loads(response.choices[0].message.content)
            inferred = result.get('inferred_endpoints', [])

            print(f"[AI] Inferred {len(inferred)} endpoints from JS code")
            return inferred

        except Exception as e:
            print(f"[!] AI JS Analysis error: {e}")
            return []

    def plan_endpoint_verification(self, endpoint_data: Dict) -> Optional[Dict]:
        """
        Create a verification plan for an inferred endpoint.

        Args:
            endpoint_data: Dictionary with url, method, parameters, reasoning

        Returns:
            Verification plan dictionary or None if planning fails
        """
        # Build user prompt with template variables
        user_prompt = self.prompts['endpoint_verification'].format(
            url=endpoint_data.get('url', ''),
            method=endpoint_data.get('method', 'GET'),
            parameters=json.dumps(endpoint_data.get('parameters', {})),
            reasoning=endpoint_data.get('reasoning', '')
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            result = json.loads(response.choices[0].message.content)
            return result.get('verification_plan')

        except Exception as e:
            print(f"[!] AI Verification planning error: {e}")
            return None

    def verify_inferred_endpoint(self, endpoint_data: Dict, timeout: int = 5) -> Tuple[bool, int, str]:
        """
        Verify an inferred endpoint with actual HTTP requests.

        Args:
            endpoint_data: Dictionary with url, method, verification_plan
            timeout: Request timeout in seconds

        Returns:
            Tuple of (exists: bool, status_code: int, message: str)
        """
        url = endpoint_data.get('url')
        method = endpoint_data.get('method', 'GET').upper()

        # Get verification plan
        verification_plan = endpoint_data.get('verification_plan')
        if not verification_plan:
            # Try to create one
            verification_plan = self.plan_endpoint_verification(endpoint_data)

        if not verification_plan:
            print(f"[!] No verification plan for {url}")
            return (False, 0, "No verification plan")

        # Try primary request
        primary = verification_plan.get('primary_request', {})
        try:
            req_method = primary.get('method', method)
            req_url = primary.get('url', url)
            req_headers = primary.get('headers', {})
            req_body = primary.get('body')
            expected_codes = primary.get('expected_codes', [200, 201, 401, 403])

            print(f"[AI Verify] {req_method} {req_url}")

            response = requests.request(
                method=req_method,
                url=req_url,
                headers=req_headers,
                json=req_body if req_body else None,
                timeout=timeout,
                verify=False,  # Allow self-signed certificates
                allow_redirects=True
            )

            status = response.status_code

            # Evaluate success based on expected codes
            if status in expected_codes:
                return (True, status, f"Endpoint verified (status: {status})")
            elif status == 404:
                return (False, status, "Endpoint does not exist (404)")
            elif status in [401, 403]:
                # Authentication required but endpoint exists
                return (True, status, f"Endpoint exists but requires auth (status: {status})")
            elif status == 405:
                # Method Not Allowed - endpoint exists but wrong method
                return (True, status, f"Endpoint exists but method not allowed (status: {status})")
            elif status >= 500:
                # Server error - endpoint exists but has internal error
                return (True, status, f"Endpoint exists but server error (status: {status})")
            else:
                # Other 4xx errors (400, 406, etc.) - likely exists but bad request
                return (True, status, f"Endpoint exists (status: {status})")

        except requests.exceptions.Timeout:
            return (False, 0, "Request timeout")
        except requests.exceptions.ConnectionError:
            return (False, 0, "Connection error")
        except Exception as e:
            return (False, 0, f"Verification error: {str(e)}")

    def analyze_js_files_batch(self, js_files: List[str], base_url: str) -> List[APIEndpoint]:
        """
        Analyze multiple JavaScript files and infer endpoints.

        Args:
            js_files: List of JavaScript file paths
            base_url: Base URL of the target

        Returns:
            List of inferred and verified APIEndpoint objects
        """
        all_inferred = []
        verified_endpoints = []

        print(f"[AI] Analyzing {len(js_files)} JavaScript files...")

        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                    js_content = f.read()

                # Infer endpoints from this file
                inferred = self.infer_endpoints_from_js(js_content, base_url, source=js_file)

                for endpoint_data in inferred:
                    # Add verification plan
                    plan = self.plan_endpoint_verification(endpoint_data)
                    if plan:
                        endpoint_data['verification_plan'] = plan

                    all_inferred.append(endpoint_data)

            except Exception as e:
                print(f"[!] Error analyzing {js_file}: {e}")
                continue

        print(f"[AI] Total inferred: {len(all_inferred)} endpoints")

        # Verify high-confidence endpoints
        print(f"[AI] Verifying inferred endpoints...")
        for endpoint_data in all_inferred:
            confidence = endpoint_data.get('confidence', 0)

            # Only verify if confidence is high enough
            if confidence >= 50:
                exists, status_code, message = self.verify_inferred_endpoint(endpoint_data)

                if exists:
                    # Convert to APIEndpoint
                    try:
                        method = HTTPMethod(endpoint_data.get('method', 'GET').upper())
                    except:
                        method = HTTPMethod.GET

                    endpoint = APIEndpoint(
                        url=endpoint_data.get('url'),
                        method=method,
                        parameters=endpoint_data.get('parameters', {}),
                        source=f"AI Inference (confidence: {confidence}%)",
                        status_code=status_code,
                        response_example=message
                    )

                    verified_endpoints.append(endpoint)
                    method_str = endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method)
                    print(f"  [✓] {method_str} {endpoint.url} (status: {status_code})")
                else:
                    print(f"  [✗] {endpoint_data.get('method')} {endpoint_data.get('url')} - {message}")

        print(f"[AI] Verified {len(verified_endpoints)} endpoints")
        return verified_endpoints


def analyze_js_with_ai(js_files: List[str], base_url: str, api_key: Optional[str] = None) -> List[APIEndpoint]:
    """
    Convenience function to analyze JS files with AI.

    Args:
        js_files: List of JavaScript file paths
        base_url: Base URL of the target
        api_key: Optional OpenAI API key

    Returns:
        List of verified APIEndpoint objects
    """
    try:
        analyzer = AIAnalyzer(api_key=api_key)
        endpoints = analyzer.analyze_js_files_batch(js_files, base_url)
        return endpoints

    except Exception as e:
        print(f"[!] AI Analysis failed: {e}")
        return []
