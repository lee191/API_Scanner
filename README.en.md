# 🔍 Route API Discovery

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/lee191/API_Scanner/actions/workflows/tests.yml/badge.svg)](https://github.com/lee191/API_Scanner/actions)

**A security analysis tool that automatically discovers hidden routes, API endpoints, and sensitive data in web applications**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-options)

</div>

---

## 📖 Overview

Route API Discovery is an automated tool for web application security analysis. It performs deep analysis of HTML and JavaScript source code to discover:

- 🔗 **Page Routes & API Endpoints** — Uncover hidden URLs and API paths
- 🔐 **Sensitive Data Detection** — Identify hardcoded tokens, passwords, API keys, and PII
- 🌐 **Dynamic Analysis** — Capture network requests executed in a real browser
- 📊 **Multiple Output Formats** — Generate JSON, XLSX, and HTML reports

### Key Features

✅ **Static Analysis** — Extract route patterns from JavaScript code  
✅ **Dynamic Analysis** — Browser automation powered by Playwright  
✅ **Recursive Scan** — Automatically follow and scan discovered pages  
✅ **Sensitive Data Detection** — 12 categories including emails, phone numbers, tokens, and PII  
✅ **GUI & CLI** — User-friendly interface and scriptable CLI  
✅ **Multi-language UI** — Korean / English  
✅ **Confidence Rating** — high / medium / low confidence assigned to every route/API candidate, with sorting and filtering  
✅ **Well-Known Discovery** — Automatically collect additional paths from `robots.txt` / `sitemap.xml`

---

## 🎯 Features

### 🔍 Static Analysis

- **JavaScript Source Analysis**
  - Collect external `<script src>` and inline `<script>` code
  - Detect `fetch()`, `axios`, and `XMLHttpRequest` patterns
  - Track dynamic `import()` and `baseURL` configurations
  - Extract route patterns from string literals

### 🌐 Dynamic Analysis (Playwright)

- **Real-time Browser Analysis**
  - Capture network requests and responses
  - Analyze JavaScript file bodies
  - Inspect DOM after rendering
  - Detect SPA router URLs

- **Automated Interaction** (optional)
  - Auto-scroll to discover lazy-loaded content
  - Automatically click links, buttons, and tabs
  - Safe browsing with a configurable action limit

### 🔐 Sensitive Data Detection

Automatically detects sensitive data across the following categories:

| Category | Examples |
|----------|---------|
| 🔑 Tokens | GitHub PAT, Stripe API Key, JWT |
| 🔒 Credentials | password, api_key, secret_key |
| 📧 Email | user@example.com |
| 📱 Phone Number | 010-1234-5678 (Korean format) |
| 👤 Name | 홍길동 (Korean), John Doe |
| 🆔 Account ID | ACCT-1234, usr_abc123 |
| 🔢 User ID | user123, uid_456 |

### 🚀 Advanced Features

- **Recursive Scan** — Automatically scan discovered pages (configurable depth)
- **Subdomain Control** — Include or exclude specific subdomains
- **Proxy Support** — Integrate with Burp Suite, OWASP ZAP, etc.
- **SSL Bypass** — Support self-signed certificate environments
- **Request Control** — Tune concurrency, delay, and timeout
- **Batch Scan** — Analyze multiple URLs simultaneously

---

## 📋 Requirements

### System Requirements

- **Python**: 3.10 or higher
- **OS**: Windows, macOS, Linux
- **Network**: Access to the target URL

### Required Packages

- `customtkinter>=5.2` — GUI framework
- `playwright>=1.44` — Browser automation
- `PySide6>=6.8` — Qt-based GUI (legacy)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Packages

```bash
pip install -e .
```

### 4. Install Playwright Browser

```bash
python -m playwright install chromium
```

---

## 💻 Usage

### Basic CLI Usage

```bash
# Basic scan
python route_api_discovery.py https://example.com

# JSON output
python route_api_discovery.py https://example.com --output result.json

# XLSX output
python route_api_discovery.py https://example.com --output result.xlsx

# HTML report
python route_api_discovery.py https://example.com --output result.html
```

### Advanced Scan Options

```bash
# Recursive scan (2 levels deep)
python route_api_discovery.py https://example.com \
  --recursive-scan \
  --recursive-depth 2

# Enable dynamic analysis
python route_api_discovery.py https://example.com \
  --dynamic-analysis \
  --dynamic-wait 5 \
  --dynamic-actions

# Use a proxy
python route_api_discovery.py https://example.com \
  --proxy http://127.0.0.1:8080

# Save JavaScript files
python route_api_discovery.py https://example.com \
  --save-js-dir ./js-files

# Disable SSL verification
python route_api_discovery.py https://example.com \
  --no-verify-ssl
```

### Launch GUI

```bash
# Method 1: Run app.py directly
python app.py

# Method 2: CLI flag
python route_api_discovery.py --gui

# Method 3: Installed command
route-api-discovery-gui
```

---

## 🎨 GUI Guide

### Main Screen Layout

1. **Target URL Input** — Enter one URL per line (batch scan supported)
2. **Scan Options**
   - Proxy settings
   - Recursive scan options
   - SSL verification settings
   - Request delay adjustment
3. **Dynamic Analysis Settings**
   - Enable Playwright
   - Automated action control
   - Wait time configuration
4. **Result Filtering**
   - Filter by category
   - Filter by severity
   - Text search

### Custom Headers

```
Authorization: Bearer token123
X-Custom-Header: value
Cookie: session=abc123
```

> **Note**: Custom headers are only sent to origins matching the input URL.

### Language Switch

Switch between Korean and English via the language menu in the top-right corner of the GUI.

---

## 📊 Output Formats

### JSON Structure

```json
{
  "input_url": "https://example.com",
  "scanned_at": "2026-06-02T09:00:00+09:00",
  "summary": {
    "js_fetched": 15,
    "page_count": 42,
    "api_count": 28,
    "sensitive_total": 8,
    "sensitive_high_or_above": 3
  },
  "js_files": [...],
  "accessible_pages": [...],
  "accessible_apis": [...],
  "sensitive_findings": [
    {
      "category": "token",
      "field_name": "api_key",
      "value": "sk_live_...",
      "masked_value": "sk_...xyz",
      "severity": "critical",
      "source_url": "https://example.com/app.js",
      "line": 42,
      "context": "const apiKey = 'sk_live_...'"
    }
  ]
}
```

### XLSX Sheet Layout

**Single Scan:**
- 📋 Summary
- 📄 JS Files
- 🔄 Dynamic Analysis
- 🌐 Pages
- 🔌 APIs
- 🔐 Sensitive Findings

**Batch Scan:**
- 📊 Batch Summary
- 📑 Result List
- 🔍 Per-URL Detail Sheets (up to 253)

### HTML Report

An interactive report viewable in any browser:
- Summary cards
- Filterable tables
- Sensitive data highlighting
- Dark / Light theme

---

## ⚙️ Options

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output file path (.json / .xlsx / .html) | stdout |
| `--timeout` | HTTP request timeout (seconds) | 10 |
| `--max-workers` | Concurrent request count | 5 |
| `--request-delay` | Delay between requests (seconds) | 0.0 |
| `--max-js-files` | Maximum number of JS files | 100 |
| `--max-depth` | JS recursive discovery depth | 3 |

### Recursive Scan

| Option | Description | Default |
|--------|-------------|---------|
| `--recursive-scan` | Enable recursive scan | False |
| `--recursive-depth` | Recursive scan depth | 1 |
| `--include-subdomains` | Include subdomains | True |
| `--exclude-subdomains` | Subdomains to exclude (comma-separated) | — |

### Dynamic Analysis

| Option | Description | Default |
|--------|-------------|---------|
| `--dynamic-analysis` | Enable dynamic analysis | False |
| `--dynamic-wait` | Wait time after page load (seconds) | 3 |
| `--dynamic-actions` | Enable automated actions | False |
| `--dynamic-action-limit` | Maximum action count | 10 |
| `--dynamic-scroll-steps` | Scroll steps | 3 |
| `--dynamic-max-events` | Maximum network events | 500 |

### Proxy & Security

| Option | Description | Default |
|--------|-------------|---------|
| `--proxy` | Proxy URL | — |
| `--no-verify-ssl` | Disable SSL verification | False |
| `--skip-probe` | Skip path accessibility check | False |

### Well-Known & Confidence

| Option | Description | Default |
|--------|-------------|---------|
| `--scan-well-known` / `--no-scan-well-known` | Scan paths from robots.txt / sitemap.xml | Enabled |
| `--min-confidence {low,medium,high}` | Exclude routes/APIs below this confidence level | low |

---

## 🧪 Testing

Run the full test suite:

```bash
python -m unittest discover -s tests -v
```

Run a specific test:

```bash
python -m unittest tests.test_route_api_discovery -v
```

### Test Coverage

- ✅ Static analysis logic
- ✅ Dynamic analysis integration
- ✅ Sensitive data detection accuracy
- ✅ URL scope validation
- ✅ Output format validation
- ✅ GUI logic

---

## 📁 Project Structure

```
API_Scanner/
├── route_api_discovery.py      # Core scan engine & CLI
├── route_api_discovery_ctk.py  # CustomTkinter GUI
├── route_api_discovery_qt.py   # PySide6 GUI (legacy)
├── app.py                       # GUI entry point
├── pyproject.toml               # Project configuration
├── GUI/
│   ├── launcher.py              # GUI launcher helper
│   └── __init__.py
├── tests/
│   ├── test_route_api_discovery.py
│   ├── test_code_review_alignment.py
│   ├── test_output_validation.py
│   └── ...
├── .github/
│   └── workflows/
│       └── tests.yml            # GitHub Actions CI
├── README.md                    # Korean documentation
└── README.en.md                 # English documentation (this file)
```

---

## ⚠️ Security & Ethical Use

### Important Notice

⚠️ **This tool must only be used against targets you have explicit permission to test.**

### Guidelines

1. **Verify Authorization**
   - Websites you own
   - Targets for which you have written permission
   - Authorized bug bounty programs

2. **Manage Result Files**
   - Output may contain plaintext sensitive data
   - Store in encrypted storage
   - Mask sensitive values before sharing

3. **Dynamic Actions Caution**
   - `--dynamic-actions` may trigger state-changing operations
   - Disable on production environments
   - Use only in test environments with limited scope

4. **Proxy & SSL**
   - Use `--proxy` and `--no-verify-ssl` only in trusted environments
   - Be aware of man-in-the-middle attack risks
   - Exercise caution when transmitting sensitive information

### Legal Disclaimer

- Users bear full responsibility for all use of this tool
- Unauthorized access and data collection may result in legal penalties
- Compliance with copyright and data privacy regulations is mandatory

---

## 🤝 Contributing

Contributions are always welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
python -m playwright install chromium
python -m unittest discover -s tests -v
```

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2026 Codex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📞 Support & Contact

- **Bug Reports**: [GitHub Issues](https://github.com/lee191/API_Scanner/issues)
- **Security Vulnerabilities**: Please report privately, not via the public issue tracker

---

<div align="center">

**Made with ❤️ for Security Researchers**

⭐ Star this repository if you find it useful!

</div>
