# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shadow API Scanner is a penetration testing tool for discovering hidden APIs in web applications through JavaScript static analysis, directory bruteforcing, and endpoint validation. It consists of:

- **CLI Scanner** (`main.py`): Command-line interface for full scans
- **Flask API Server** (`api_server.py`): REST API that wraps CLI scanner for web UI
- **Next.js Web UI** (`web-ui/`): Modern dashboard for scan management
- **SQLite Database**: Scan history, endpoints, vulnerabilities, projects

## Development Commands

### Running the Application

```bash
# Terminal 1: Start Flask API server (required for web UI)
python api_server.py
# Runs on http://localhost:5001

# Terminal 2: Start Next.js web UI
cd web-ui
npm run dev
# Runs on http://localhost:3000

# Terminal 3 (optional): Start test application
cd test-app
python app.py
# Runs on http://localhost:5000
```

### CLI Scanner

```bash
# Full scan with validation (ALWAYS use --validate for status_code)
python main.py full-scan http://localhost:5000 \
  --js-path ./test-app/static \
  --validate \
  --bruteforce \
  --output output/

# JavaScript-only analysis
python main.py analyze ./test-app/static --base-url http://localhost:5000

# Database initialization (if needed)
python setup_db.py
```

### Web UI Development

```bash
cd web-ui

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Critical Architecture Patterns

### 1. Dual-Layer Data Models

**THIS IS CRUCIAL**: The codebase uses TWO separate model systems that must stay synchronized:

- **Pydantic Models** (`src/utils/models.py`): Used by CLI scanner for validation and JSON serialization
  - `APIEndpoint`, `Vulnerability`, `ScanResult`
  - Have `use_enum_values = True` - enums are automatically converted to strings

- **SQLAlchemy Models** (`src/database/models.py`): Used for database persistence
  - `Endpoint`, `Vulnerability`, `Scan`, `Project`, `DiscoveredPath`
  - Have `to_dict()` methods for API responses

**Common Bug Pattern**: When adding fields, you MUST update:
1. Pydantic model in `src/utils/models.py`
2. SQLAlchemy model in `src/database/models.py`
3. Repository save/load logic in `src/database/repository.py`
4. API server JSON-to-Pydantic conversion in `api_server.py` (lines 88-101)

Example from recent bug fix:
```python
# api_server.py - MUST include ALL fields when creating Pydantic objects
ep = APIEndpoint(
    url=ep_data['url'],
    method=HTTPMethod[ep_data['method'].upper()],
    parameters=ep_data.get('parameters', {}),
    source=ep_data.get('source', 'unknown'),
    headers=ep_data.get('headers', {}),
    body_example=ep_data.get('body_example'),
    response_example=ep_data.get('response_example'),
    poc_code=ep_data.get('poc_code'),
    status_code=ep_data.get('status_code')  # This was missing and caused bugs!
)
```

### 2. Scanner Execution Flow

The web UI triggers scans through a subprocess pattern:

```
Web UI (localhost:3000)
  ↓ HTTP POST /api/scan
Flask API Server (localhost:5001)
  ↓ execute_scan_async() in background thread
  ↓ subprocess: python main.py full-scan --validate --output ...
CLI Scanner (main.py)
  ↓ Collects JS → Analyzes → Validates HTTP → Generates JSON
  ↓ Saves to output/web-scans/{scan_id}/
Flask API Server
  ↓ Reads JSON → Creates Pydantic objects → Saves to SQLite
  ↓ Returns scan_id to client
Web UI
  ↓ Polls GET /api/status/{scan_id}
```

**CRITICAL**: The `--validate` flag MUST be passed to populate `status_code`. API server always adds this (api_server.py:58).

### 3. Shadow API Classification System

Located in `src/utils/api_classifier.py`, this is a **multi-criteria intelligent classifier** (NOT simple source-based):

**6-Step Classification Logic**:
1. Check if from official docs (OpenAPI/Swagger) → Public unless matches shadow patterns
2. Check URL shadow patterns (`/internal/`, `/admin/`, `/debug/`, etc.)
3. Check URL public patterns (`/api/v\d+/auth/`, `/login`, `/register`)
4. Check sensitive operations (DELETE/PUT on `/users/`, `/admin/`, etc.)
5. Check response indicators (401/403 on admin paths, sensitive data in response)
6. **Default to Shadow if uncertain** (conservative security-first approach)

**Used in two places**:
- `src/database/repository.py:212` - When saving endpoints to database
- `src/reporter/report_generator.py:13-15` - When generating reports

**Never use simple source-based logic**: `source not in ['documentation', 'openapi']`

### 4. Endpoint Validation Critical Details

`src/utils/endpoint_validator.py` validates endpoints with HTTP requests:

**Pydantic Enum Handling Bug Pattern**:
```python
# WRONG - Fails if Pydantic converted enum to string
method = endpoint.method.value

# CORRECT - Check type first
method = endpoint.method if isinstance(endpoint.method, str) else endpoint.method.value
```

This is because `use_enum_values = True` in Pydantic models means `endpoint.method` is already a string, not an enum object.

**Validation updates endpoint in-place**:
```python
# main.py:246-247
endpoint.status_code = status_code  # HTTP validation populates this
endpoint.response_example = response
```

### 5. Database Context Manager Pattern

All database operations use context manager for safety:

```python
from src.database import get_db

# ALWAYS use context manager
with get_db() as db:
    result = ScanRepository.get_scan_with_details(db, scan_id)
    # db.commit() called automatically on success
    # db.rollback() called automatically on exception
```

**Repository Pattern**: All DB operations go through `ProjectRepository` or `ScanRepository` classes - never use raw SQLAlchemy queries except in complex analytics.

### 6. KST Timezone Handling

All timestamps use Korea Standard Time (UTC+9):

```python
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST)
```

This is defined identically in:
- `src/utils/models.py`
- `src/database/models.py`
- `main.py`

**Always use `get_kst_now()` for timestamps**, not `datetime.now()`.

### 7. Windows UTF-8 Encoding Fix

**Required at top of all entry points**:

```python
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

This prevents encoding errors with Korean (한글) characters in output.

## Module Responsibilities

### src/crawler/
- `js_collector.py`: Downloads JS files from target URL, handles bruteforcing
- `directory_bruteforcer.py`: Wordlist-based directory discovery

### src/analyzer/
- `js_analyzer.py`: Regex + AST-based JavaScript parsing for API endpoints
- `endpoint_collector.py`: Deduplicates and aggregates discovered endpoints

### src/utils/
- `api_classifier.py`: Shadow/Public API classification (multi-criteria)
- `endpoint_validator.py`: HTTP validation to populate status_code
- `curl_generator.py`: Generates curl commands for endpoints
- `models.py`: Pydantic data models (APIEndpoint, Vulnerability, ScanResult)

### src/database/
- `models.py`: SQLAlchemy ORM models (Scan, Endpoint, Vulnerability, Project)
- `repository.py`: Data access layer (ProjectRepository, ScanRepository)
- `connection.py`: Database connection and session management

### src/reporter/
- `report_generator.py`: Generates JSON/HTML/Markdown reports

## Testing the Full Stack

```bash
# 1. Start test app (vulnerable Flask app)
cd test-app
python app.py  # localhost:5000

# 2. Start API server
python api_server.py  # localhost:5001

# 3. Start web UI
cd web-ui
npm run dev  # localhost:3000

# 4. Run scan through web UI
# Navigate to http://localhost:3000
# Enter target: http://localhost:5000
# Enable: Validate Endpoints
# Click: Start Scan

# Expected results:
# - 15+ endpoints discovered
# - Shadow APIs: ~18 (includes /api/internal/*, /admin/*, etc.)
# - Public APIs: ~2 (/login, /register)
# - status_code displayed as colored badges in UI
```

## Common Bugs and Patterns

### Bug: status_code is null in database

**Root Cause**: Field not propagated through all layers

**Check**:
1. CLI scanner: `main.py:246` - Does validation update `endpoint.status_code`?
2. Report JSON: Does `output/*/scan.json` contain `"status_code": 404`?
3. API server: `api_server.py:98` - Is `status_code` passed to `APIEndpoint(...)`?
4. Repository: `src/database/repository.py:232` - Is `status_code=ep.status_code` in Endpoint constructor?
5. Web UI: Does API response contain `status_code`?

### Bug: All endpoints classified as Shadow

**Root Cause**: Using old simple source-based logic instead of intelligent classifier

**Fix**: Always use `APIClassifier.classify(endpoint, source=endpoint.source)`

### Bug: Enum attribute error

**Root Cause**: Pydantic `use_enum_values = True` converts enums to strings

**Fix**: Type-check before accessing `.value`:
```python
method = endpoint.method if isinstance(endpoint.method, str) else endpoint.method.value
```

## Configuration Files

- `config/config.yaml`: Scanner configuration (not currently used)
- `.env`: Environment variables (DATABASE_URL, etc.)
- `data/scanner.db`: SQLite database (gitignored)
- `output/`: Scan reports (gitignored)

## Security Notes

**This tool is for defensive security only**. Use only on systems you own or have explicit permission to test.

## Database Schema Quick Reference

```
projects (id, project_id UUID, name, description, timestamps)
  ↓ one-to-many
scans (id, scan_id UUID, project_id FK, target_url, status, progress, statistics, timestamps)
  ↓ one-to-many
endpoints (id, scan_id FK, url, method, is_shadow_api, status_code, parameters, headers, source, timestamp)
vulnerabilities (id, scan_id FK, type, level, endpoint, description, evidence, cwe_id, timestamp)
discovered_paths (id, scan_id FK, path, status_code, content_length, content_type, timestamp)
```

All use `cascade="all, delete-orphan"` - deleting a scan deletes all related endpoints/vulnerabilities.
