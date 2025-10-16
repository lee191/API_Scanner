"""Report generation for scan results."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from jinja2 import Template
from src.utils.models import ScanResult, VulnerabilityLevel
from src.utils.curl_generator import CurlGenerator
from src.utils.api_classifier import APIClassifier


def is_shadow_api(endpoint) -> bool:
    """Determine if an endpoint is a shadow API using intelligent classifier."""
    return APIClassifier.classify(endpoint, source=endpoint.source)


class ReportGenerator:
    """Generate reports in various formats."""

    def __init__(self, output_dir: str = "output"):
        """Initialize report generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_all(self, scan_result: ScanResult, prefix: str = "scan"):
        """Generate reports in all formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{prefix}_{timestamp}"

        reports = {
            'json': self.generate_json(scan_result, base_name),
            'html': self.generate_html(scan_result, base_name),
            'markdown': self.generate_markdown(scan_result, base_name),
        }

        return reports

    def generate_json(self, scan_result: ScanResult, filename: str = "scan") -> str:
        """Generate JSON report."""
        output_path = self.output_dir / f"{filename}.json"

        # Shadow API 분류
        shadow_endpoints = []
        public_endpoints = []

        for ep in scan_result.endpoints:
            ep_data = {
                'url': ep.url,
                'method': ep.method,
                'parameters': ep.parameters,
                'source': ep.source,
                'status_code': ep.status_code,
                'is_shadow_api': is_shadow_api(ep)
            }

            if ep_data['is_shadow_api']:
                shadow_endpoints.append(ep_data)
            else:
                public_endpoints.append(ep_data)

        # 취약점에 PoC 추가
        vulnerabilities_with_poc = []
        for vuln in scan_result.vulnerabilities:
            vuln_data = {
                'type': vuln.type,
                'level': vuln.level,
                'endpoint': vuln.endpoint,
                'method': vuln.method,
                'description': vuln.description,
                'evidence': vuln.evidence,
                'recommendation': vuln.recommendation,
                'cwe_id': vuln.cwe_id,
                'poc': ''  # PoC generation removed
            }
            vulnerabilities_with_poc.append(vuln_data)

        report_data = {
            'target': scan_result.target,
            'scan_start': scan_result.scan_start.isoformat(),
            'scan_end': scan_result.scan_end.isoformat() if scan_result.scan_end else None,
            'statistics': {
                **scan_result.statistics,
                'shadow_apis': len(shadow_endpoints),
                'public_apis': len(public_endpoints)
            },
            'discovered_paths': scan_result.discovered_paths,
            'shadow_apis': shadow_endpoints,
            'public_apis': public_endpoints,
            'all_endpoints': [
                {
                    'url': ep.url,
                    'method': ep.method,
                    'parameters': ep.parameters,
                    'source': ep.source,
                    'status_code': ep.status_code,
                    'is_shadow_api': is_shadow_api(ep)
                }
                for ep in scan_result.endpoints
            ],
            'vulnerabilities': vulnerabilities_with_poc
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"[+] JSON report: {output_path}")
        print(f"    - Shadow APIs: {len(shadow_endpoints)}")
        print(f"    - Public APIs: {len(public_endpoints)}")
        print(f"    - Vulnerabilities with PoC: {len(vulnerabilities_with_poc)}")
        return str(output_path)

    def generate_markdown(self, scan_result: ScanResult, filename: str = "scan") -> str:
        """Generate Markdown report."""
        output_path = self.output_dir / f"{filename}.md"

        template = """# Shadow API Scan Report

## Scan Information
- **Target**: {{ target }}
- **Start Time**: {{ scan_start }}
- **End Time**: {{ scan_end }}
- **Duration**: {{ duration }}

## Summary Statistics
- **Total Endpoints**: {{ stats.total_endpoints }}
  - 🔒 **Shadow APIs**: {{ stats.shadow_apis }} (숨겨진/문서화되지 않은 API)
  - 🌐 **Public APIs**: {{ stats.public_apis }} (공개된 API)
- **Total Vulnerabilities**: {{ stats.total_vulnerabilities }}
  - 🔴 Critical: {{ stats.critical }}
  - 🟠 High: {{ stats.high }}
  - 🟡 Medium: {{ stats.medium }}
  - 🟢 Low: {{ stats.low }}
{% if stats.discovered_paths > 0 %}
- **Discovered Paths**: {{ stats.discovered_paths }} (브루트포싱으로 발견된 경로)
{% endif %}

---

{% if discovered_paths %}
## 🔍 Discovered Paths (브루트포싱으로 발견된 경로)

브루트포싱을 통해 발견된 숨겨진 경로들입니다:

{% for path in discovered_paths %}
- `{{ path }}`
{% endfor %}

---
{% endif %}

## 🔒 Shadow APIs (숨겨진/문서화되지 않은 API)

{% if shadow_endpoints %}
{% for endpoint in shadow_endpoints %}
### {{ endpoint.method }} `{{ endpoint.url }}`
- **Source**: {{ endpoint.source }}
- **Status**: {{ endpoint.status_code or 'N/A' }}
- **Parameters**: {% if endpoint.parameters %}{{ endpoint.parameters|length }}{% else %}None{% endif %}
- **⚠️ Warning**: 이 엔드포인트는 문서화되지 않았거나 내부용으로 보입니다

{% if endpoint.parameters %}
**Parameters:**
{% for param, ptype in endpoint.parameters.items() %}
- `{{ param }}`: {{ ptype }}
{% endfor %}
{% endif %}

{% endfor %}
{% else %}
✅ Shadow API가 발견되지 않았습니다.
{% endif %}

---

## 🌐 Public APIs (공개된 API)

{% if public_endpoints %}
{% for endpoint in public_endpoints %}
### {{ endpoint.method }} `{{ endpoint.url }}`
- **Source**: {{ endpoint.source }}
- **Status**: {{ endpoint.status_code or 'N/A' }}
- **Parameters**: {% if endpoint.parameters %}{{ endpoint.parameters|length }}{% else %}None{% endif %}

{% if endpoint.parameters %}
**Parameters:**
{% for param, ptype in endpoint.parameters.items() %}
- `{{ param }}`: {{ ptype }}
{% endfor %}
{% endif %}

{% endfor %}
{% else %}
❌ Public API가 발견되지 않았습니다.
{% endif %}

---

## Security Vulnerabilities

{% if vulnerabilities %}
{% for vuln in vulnerabilities %}
### {% if vuln.level == 'critical' %}🔴{% elif vuln.level == 'high' %}🟠{% elif vuln.level == 'medium' %}🟡{% else %}🟢{% endif %} {{ vuln.type }} [{{ vuln.level|upper }}]

**Endpoint**: `{{ vuln.method }} {{ vuln.endpoint }}`
**CWE**: {{ vuln.cwe_id or 'N/A' }}

**Description**:
{{ vuln.description }}

**Evidence**:
{{ vuln.evidence }}

**Recommendation**:
{{ vuln.recommendation }}

**PoC (Proof of Concept)**:
```python
{{ vuln.poc }}
```

---

{% endfor %}
{% else %}
✅ No vulnerabilities detected.
{% endif %}

---

## Endpoint Groups

{% for group, eps in endpoint_groups.items() %}
### {{ group }} ({{ eps|length }} endpoints)
{% for ep in eps %}
- {{ ep.method }} `{{ ep.url }}`{% if ep.is_shadow_api %} 🔒{% endif %}
{% endfor %}

{% endfor %}

---

*Report generated by Shadow API Scanner*
*{{ timestamp }}*
"""

        # Calculate duration
        duration = "N/A"
        if scan_result.scan_end:
            delta = scan_result.scan_end - scan_result.scan_start
            duration = f"{delta.total_seconds():.2f} seconds"

        # Shadow API 분류
        shadow_endpoints = []
        public_endpoints = []
        endpoints_with_classification = []

        for ep in scan_result.endpoints:
            is_shadow = is_shadow_api(ep)
            ep_data = {
                'url': ep.url,
                'method': ep.method,
                'parameters': ep.parameters,
                'source': ep.source,
                'status_code': ep.status_code,
                'is_shadow_api': is_shadow
            }
            endpoints_with_classification.append(ep_data)

            if is_shadow:
                shadow_endpoints.append(ep_data)
            else:
                public_endpoints.append(ep_data)

        # 취약점에 PoC 추가
        vulnerabilities_with_poc = []
        for vuln in scan_result.vulnerabilities:
            vuln_data = {
                'type': vuln.type,
                'level': vuln.level,
                'endpoint': vuln.endpoint,
                'method': vuln.method,
                'description': vuln.description,
                'evidence': vuln.evidence,
                'recommendation': vuln.recommendation,
                'cwe_id': vuln.cwe_id,
                'poc': ''  # PoC generation removed
            }
            vulnerabilities_with_poc.append(vuln_data)

        # Group endpoints
        from src.analyzer.endpoint_collector import EndpointCollector
        collector = EndpointCollector()
        collector.add_endpoints(scan_result.endpoints)
        endpoint_groups = {}
        for group, eps in collector.group_by_path().items():
            endpoint_groups[group] = [{
                'method': ep.method,
                'url': ep.url,
                'is_shadow_api': is_shadow_api(ep)
            } for ep in eps]

        # 통계에 Shadow API 정보 추가
        stats = {
            **scan_result.statistics,
            'shadow_apis': len(shadow_endpoints),
            'public_apis': len(public_endpoints)
        }

        # Render template
        tmpl = Template(template)
        content = tmpl.render(
            target=scan_result.target,
            scan_start=scan_result.scan_start.strftime("%Y-%m-%d %H:%M:%S"),
            scan_end=scan_result.scan_end.strftime("%Y-%m-%d %H:%M:%S") if scan_result.scan_end else "N/A",
            duration=duration,
            stats=stats,
            discovered_paths=scan_result.discovered_paths,
            shadow_endpoints=shadow_endpoints,
            public_endpoints=public_endpoints,
            endpoints=endpoints_with_classification,
            vulnerabilities=vulnerabilities_with_poc,
            endpoint_groups=endpoint_groups,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[+] Markdown report: {output_path}")
        print(f"    - Shadow APIs: {len(shadow_endpoints)}")
        print(f"    - Public APIs: {len(public_endpoints)}")
        return str(output_path)

    def generate_html(self, scan_result: ScanResult, filename: str = "scan") -> str:
        """Generate HTML report."""
        output_path = self.output_dir / f"{filename}.html"

        template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shadow API Scan Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
        h2 { color: #34495e; margin-top: 30px; margin-bottom: 15px; border-left: 4px solid #3498db; padding-left: 10px; }
        h3 { color: #555; margin-top: 20px; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-box h3 { color: white; margin: 0; font-size: 14px; }
        .stat-box .number { font-size: 32px; font-weight: bold; margin: 10px 0; }
        .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
        .method { display: inline-block; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-right: 10px; }
        .method.GET { background: #3498db; color: white; }
        .method.POST { background: #2ecc71; color: white; }
        .method.PUT { background: #f39c12; color: white; }
        .method.DELETE { background: #e74c3c; color: white; }
        .vulnerability { padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 5px solid; }
        .vulnerability.critical { background: #ffe5e5; border-color: #c0392b; }
        .vulnerability.high { background: #fff3e5; border-color: #e67e22; }
        .vulnerability.medium { background: #fffbe5; border-color: #f39c12; }
        .vulnerability.low { background: #e8f8f5; border-color: #16a085; }
        .level-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 12px; margin-left: 10px; }
        .level-badge.critical { background: #c0392b; color: white; }
        .level-badge.high { background: #e67e22; color: white; }
        .level-badge.medium { background: #f39c12; color: white; }
        .level-badge.low { background: #16a085; color: white; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }
        .params { margin-top: 10px; }
        .param-item { background: white; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; text-align: center; color: #7f8c8d; }
        .shadow-api { border-left-color: #e74c3c !important; background: #fff5f5; }
        .shadow-badge { background: #e74c3c; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 10px; }
        .poc-code { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre; font-family: 'Courier New', monospace; font-size: 13px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Shadow API Scan Report</h1>

        <div class="stats">
            <div class="stat-box">
                <h3>총 엔드포인트</h3>
                <div class="number">{{ stats.total_endpoints }}</div>
                <div style="font-size: 12px; margin-top: 5px;">Shadow: {{ stats.shadow_apis }} | Public: {{ stats.public_apis }}</div>
            </div>
            <div class="stat-box">
                <h3>총 취약점</h3>
                <div class="number">{{ stats.total_vulnerabilities }}</div>
            </div>
            <div class="stat-box">
                <h3>위험 취약점</h3>
                <div class="number">{{ stats.critical + stats.high }}</div>
            </div>
            <div class="stat-box">
                <h3>스캔 소요 시간</h3>
                <div class="number">{{ duration }}</div>
            </div>
        </div>

        <h2>📊 스캔 정보</h2>
        <table>
            <tr><th>항목</th><th>값</th></tr>
            <tr><td>대상</td><td><code>{{ target }}</code></td></tr>
            <tr><td>시작 시간</td><td>{{ scan_start }}</td></tr>
            <tr><td>종료 시간</td><td>{{ scan_end }}</td></tr>
        </table>

        {% if discovered_paths %}
        <h2>🔍 Discovered Paths (브루트포싱으로 발견된 경로)</h2>
        <p style="color:#7f8c8d; margin-bottom:15px;">브루트포싱을 통해 발견된 숨겨진 경로들입니다:</p>
        <div style="background:#f8f9fa; padding:20px; border-radius:8px; border-left:4px solid #3498db;">
            {% for path in discovered_paths %}
            <div style="background:white; padding:10px; margin:5px 0; border-radius:4px; font-family:'Courier New',monospace;">
                🔗 <code>{{ path }}</code>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <h2>🔒 Shadow APIs (숨겨진/문서화되지 않은 API)</h2>
        {% if shadow_endpoints %}
        {% for endpoint in shadow_endpoints %}
        <div class="endpoint shadow-api">
            <span class="method {{ endpoint.method }}">{{ endpoint.method }}</span>
            <code>{{ endpoint.url }}</code>
            <span class="shadow-badge">🔒 SHADOW API</span>
            <div style="margin-top:10px; font-size:13px; color:#7f8c8d;">
                📍 Source: {{ endpoint.source }} |
                {% if endpoint.status_code %}Status: {{ endpoint.status_code }}{% else %}Status: N/A{% endif %}
            </div>
            <div style="margin-top:8px; color:#c0392b; font-size:13px; font-weight:bold;">
                ⚠️ 이 엔드포인트는 문서화되지 않았거나 내부용으로 보입니다
            </div>
            {% if endpoint.parameters %}
            <div class="params">
                <strong>파라미터:</strong>
                {% for param, ptype in endpoint.parameters.items() %}
                <div class="param-item">• <code>{{ param }}</code>: {{ ptype }}</div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p style="color:#27ae60;">✅ Shadow API가 발견되지 않았습니다.</p>
        {% endif %}

        <h2>🌐 Public APIs (공개된 API)</h2>
        {% if public_endpoints %}
        {% for endpoint in public_endpoints %}
        <div class="endpoint">
            <span class="method {{ endpoint.method }}">{{ endpoint.method }}</span>
            <code>{{ endpoint.url }}</code>
            <div style="margin-top:10px; font-size:13px; color:#7f8c8d;">
                📍 Source: {{ endpoint.source }} |
                {% if endpoint.status_code %}Status: {{ endpoint.status_code }}{% else %}Status: N/A{% endif %}
            </div>
            {% if endpoint.parameters %}
            <div class="params">
                <strong>파라미터:</strong>
                {% for param, ptype in endpoint.parameters.items() %}
                <div class="param-item">• <code>{{ param }}</code>: {{ ptype }}</div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p style="color:#e67e22;">❌ Public API가 발견되지 않았습니다.</p>
        {% endif %}

        <h2>🛡️ 보안 취약점</h2>
        {% if vulnerabilities %}
        {% for vuln in vulnerabilities %}
        <div class="vulnerability {{ vuln.level }}">
            <h3>
                {{ vuln.type }}
                <span class="level-badge {{ vuln.level }}">{{ vuln.level|upper }}</span>
            </h3>
            <p><strong>엔드포인트:</strong> <code>{{ vuln.method }} {{ vuln.endpoint }}</code></p>
            {% if vuln.cwe_id %}<p><strong>CWE:</strong> {{ vuln.cwe_id }}</p>{% endif %}
            <p><strong>설명:</strong> {{ vuln.description }}</p>
            <p><strong>증거:</strong> {{ vuln.evidence }}</p>
            <p><strong>권장사항:</strong> {{ vuln.recommendation }}</p>
            {% if vuln.poc %}
            <details style="margin-top: 15px;">
                <summary style="cursor: pointer; font-weight: bold; color: #2c3e50;">🔍 PoC (Proof of Concept) 코드 보기</summary>
                <div class="poc-code">{{ vuln.poc }}</div>
            </details>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p style="color:#27ae60; font-size:18px;">✅ 발견된 취약점이 없습니다.</p>
        {% endif %}

        <div class="footer">
            <p>Shadow API Scanner | Generated: {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>"""

        # Calculate duration
        duration = "N/A"
        if scan_result.scan_end:
            delta = scan_result.scan_end - scan_result.scan_start
            duration = f"{delta.total_seconds():.1f}s"

        # Shadow API 분류
        shadow_endpoints = []
        public_endpoints = []

        for ep in scan_result.endpoints:
            is_shadow = is_shadow_api(ep)
            ep_data = {
                'url': ep.url,
                'method': ep.method,
                'parameters': ep.parameters,
                'source': ep.source,
                'status_code': ep.status_code,
                'is_shadow_api': is_shadow
            }

            if is_shadow:
                shadow_endpoints.append(ep_data)
            else:
                public_endpoints.append(ep_data)

        # 취약점에 PoC 추가
        vulnerabilities_with_poc = []
        for vuln in scan_result.vulnerabilities:
            vuln_data = {
                'type': vuln.type,
                'level': vuln.level,
                'endpoint': vuln.endpoint,
                'method': vuln.method,
                'description': vuln.description,
                'evidence': vuln.evidence,
                'recommendation': vuln.recommendation,
                'cwe_id': vuln.cwe_id,
                'poc': ''  # PoC generation removed
            }
            vulnerabilities_with_poc.append(vuln_data)

        # 통계에 Shadow API 정보 추가
        stats = {
            **scan_result.statistics,
            'shadow_apis': len(shadow_endpoints),
            'public_apis': len(public_endpoints)
        }

        # Render template
        tmpl = Template(template)
        content = tmpl.render(
            target=scan_result.target,
            scan_start=scan_result.scan_start.strftime("%Y-%m-%d %H:%M:%S"),
            scan_end=scan_result.scan_end.strftime("%Y-%m-%d %H:%M:%S") if scan_result.scan_end else "N/A",
            duration=duration,
            stats=stats,
            discovered_paths=scan_result.discovered_paths,
            shadow_endpoints=shadow_endpoints,
            public_endpoints=public_endpoints,
            endpoints=scan_result.endpoints,
            vulnerabilities=vulnerabilities_with_poc,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[+] HTML report: {output_path}")
        print(f"    - Shadow APIs: {len(shadow_endpoints)}")
        print(f"    - Public APIs: {len(public_endpoints)}")
        return str(output_path)
