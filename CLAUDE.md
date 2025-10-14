# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shadow API Scanner is a defensive penetration testing tool for discovering undocumented/shadow APIs and analyzing security vulnerabilities in web applications. It combines network traffic capture, JavaScript static analysis, and OWASP-based vulnerability scanning.

**⚠️ Security Context**: This is a defensive security tool. All development must align with ethical security research - assist with vulnerability detection and defensive measures only, never with malicious exploitation.

## Core Architecture

### Pipeline Flow
1. **Collection Phase**: Proxy capture (mitmproxy) OR JavaScript static analysis (esprima/regex)
2. **Analysis Phase**: Extract API endpoints from network traffic or JS source code
3. **Scanning Phase**: Test endpoints for OWASP Top 10 vulnerabilities (SQL injection, XSS, auth issues, CORS misconfig, etc.)
4. **Reporting Phase**: Generate JSON/HTML/Markdown reports with vulnerability details and remediation guidance

### Module Organization
```
src/
├── proxy/              → mitmproxy-based traffic capture (ProxyRunner)
├── crawler/            → JS file discovery and download (JSCollector)
├── analyzer/           → Static analysis of JavaScript (JSAnalyzer, EndpointCollector, AIJSAnalyzer)
├── scanner/            → Vulnerability testing (VulnerabilityScanner)
├── reporter/           → Multi-format report generation (ReportGenerator)
├── database/           → PostgreSQL/SQLite persistence (models, connection, repository)
└── utils/              → Shared models (APIEndpoint, Vulnerability, ScanResult)
```

**Key Pattern**: Each pipeline stage is independent - endpoints flow from collectors → analyzer → scanner → reporter via `EndpointCollector` and `ScanResult` models (Pydantic-based).

### API Server Integration
- **Flask API** (`api_server.py`): REST endpoints for web UI integration
- **Async Scanning**: Background thread execution with database status tracking
- **Web UI Communication**: Spawns Python CLI processes, monitors progress via database
- **Port**: API server runs on `http://localhost:5001` by default

### Data Models (src/utils/models.py)
- **APIEndpoint**: URL, HTTP method, parameters, headers, source tracking, response examples, **PoC code**
- **Vulnerability**: Type, severity level (CRITICAL/HIGH/MEDIUM/LOW), CWE mapping, evidence, recommendations, **PoC code**
- **ScanResult**: Aggregates endpoints + vulnerabilities with statistics and timestamps

### AI-Powered Analysis (src/analyzer/ai_analyzer.py)
**NEW FEATURE**: Optional OpenAI integration for enhanced endpoint discovery and PoC generation.

**Capabilities**:
- **Smart Endpoint Extraction**: Uses GPT-4 to analyze complex JavaScript patterns beyond regex
- **PoC Code Generation**: Auto-generates Python `requests` code for testing endpoints
- **Vulnerability PoC**: Creates exploitation PoC for discovered vulnerabilities
- **Template Variable Cleaning**: Replaces `${id}`, `:id` patterns with concrete values (123, 'testuser', etc.)

**Configuration** (via `.env`):
```bash
OPENAI_API_KEY=sk-...                  # Required for AI features
OPENAI_MODEL=gpt-4-turbo-preview       # Default model
AI_ANALYSIS_ENABLED=true               # Enable/disable AI features
AI_MAX_TOKENS=8000                     # Max tokens per request
```

**Usage Pattern**:
- AI analyzer runs automatically in `full-scan` if API key is configured
- Generates PoC code for all endpoints and vulnerabilities
- Fallback to regex-based analysis if AI is disabled or fails
- PoC code is stored in `poc_code` field of `APIEndpoint` and `Vulnerability` models

**Cost Management**:
- Limits to first 10 vulnerabilities for PoC generation
- Uses `temperature=0.1-0.2` for consistent output
- Truncates large code samples to 8000 chars

### JavaScript Analysis Strategy (src/analyzer/js_analyzer.py)
- **Regex Patterns**: Detects `fetch()`, `axios`, `XMLHttpRequest`, jQuery `$.ajax`, hardcoded API URLs
- **Template Variable Handling**: Converts `${param}` or `{param}` → `:param` for parameterized endpoints
- **AST Parsing**: Fallback to esprima for complex JavaScript (tolerant parsing for partial/minified code)
- **Shadow API Detection**: Flags endpoints with `/internal/`, `/admin/`, `/debug/`, `/_`, `/v0/`, etc.

### Vulnerability Scanner (src/scanner/vulnerability_scanner.py)
**Implemented Checks**:
- Missing/weak authentication (unauthenticated 200 responses)
- CORS misconfigurations (wildcard origins, reflected origins with credentials)
- Sensitive data exposure (password/API key patterns in URLs/responses)
- SQL injection (error message detection via payloads like `'`, `1' OR '1'='1`)
- XSS (unescaped script tag reflection)
- Rate limiting (burst request testing)

**Detection Method**: Sends test requests with security payloads, analyzes responses for vulnerability indicators (error messages, header values, status codes).

## Development Commands

### Setup
```bash
# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Playwright browsers (optional, for web crawling)
playwright install

# Configure AI features (optional)
cp .env.example .env
# Edit .env and add OPENAI_API_KEY if using AI analysis

# Database setup (optional - for API server and persistence)
python setup_db.py
# Choose SQLite (default) or PostgreSQL in .env
```

### Testing with Vulnerable Test App
```bash
# Start Docker test environment
./docker-run.sh          # Linux/Mac
docker-run.bat           # Windows

# Run integration tests
./test-scripts/run-test.sh      # Linux/Mac
test-scripts\run-test.bat       # Windows

# Manual testing
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns \
  --output output

# Stop test environment
./docker-stop.sh         # Linux/Mac
docker-stop.bat          # Windows
```

### CLI Usage Patterns
```bash
# JavaScript-only analysis
python main.py analyze <file_or_directory> \
  --base-url https://example.com \
  --recursive

# Full scan (JS analysis + vulnerability testing)
python main.py full-scan <target_url> \
  --js-path <static_directory> \
  --scan-vulns \
  --output <report_directory>

# Proxy mode (network traffic capture)
python main.py proxy --host 127.0.0.1 --port 8080
# Then configure browser proxy to 127.0.0.1:8080
```

### Full Stack Development Workflow
**Running Complete System** (API Server + Web UI):
```bash
# Terminal 1: Start Flask API Server
python api_server.py
# Listens on http://localhost:5001

# Terminal 2: Start Next.js Web UI
cd web-ui
npm run dev
# Listens on http://localhost:3000

# Access web interface at http://localhost:3000
# Web UI communicates with API server automatically
```

**Database-backed vs CLI-only**:
- **CLI mode** (`python main.py`): Direct execution, no database, immediate JSON/HTML reports
- **Web UI mode** (`api_server.py`): Database-backed, async execution, progress tracking, scan history

### API Server (Flask Backend)
```bash
# Start Flask API server (required for web UI)
python api_server.py
# Runs on http://localhost:5001

# API endpoints:
# POST /api/scan              - Start new scan
# GET  /api/status/<scan_id>  - Get scan progress/results
# GET  /api/history           - Get scan history
# DELETE /api/scan/<scan_id>  - Delete scan
# GET  /health                - Health check
```

### Web UI (Next.js Frontend)
```bash
cd web-ui
npm install
npm run dev      # Development server on http://localhost:3000
npm run build    # Production build
npm start        # Production server
npm run lint     # ESLint
```

**Web UI Integration**:
- **Frontend → API Server**: Web UI calls Flask API at `http://localhost:5001`
- **API Server → Scanner**: Spawns Python CLI processes via `subprocess`, monitors via database
- **Real-time Updates**: Polls `/api/status/<scan_id>` for progress (database-backed status)
- **Scan Persistence**: Results stored in database (`data/scanner.db` or PostgreSQL)

## Configuration

### config/config.yaml
Central configuration for proxy settings, JS analysis patterns, scanner checks, output formats. Supports local overrides via `config/config.local.yaml` (gitignored).

**Key Settings**:
- `proxy.timeout`: Network request timeout (default: 30s)
- `scanner.timeout`: Vulnerability test timeout (default: 10s)
- `output.formats`: Report types (`json`, `html`, `markdown`)

### .env (Environment Variables)
**AI Features**:
```bash
OPENAI_API_KEY=sk-...             # OpenAI API key (required for AI analysis)
OPENAI_MODEL=gpt-4-turbo-preview  # GPT model to use
AI_ANALYSIS_ENABLED=true          # Enable/disable AI features
AI_MAX_TOKENS=8000                # Max tokens per AI request
```

**Database** (for API server):
```bash
# SQLite (default - zero config)
DATABASE_URL=sqlite:///data/scanner.db

# PostgreSQL (optional - for production)
DATABASE_URL=postgresql://user:password@localhost:5432/shadow_api_scanner
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shadow_api_scanner
DB_USER=postgres
DB_PASSWORD=your_password
```

**Note**: Use `.env.example` as template. Never commit `.env` with credentials.

## Code Style and Patterns

### Python Conventions
- **PEP 8**: 4-space indentation, max 100 characters per line preferred
- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Type Hints**: Use for public APIs and Pydantic models
- **Error Handling**: Graceful degradation with `try/except`, continue scanning on individual endpoint failures
- **Logging**: Use `logging` module for operational code, avoid `print()` except in CLI output formatting

### CLI Extensions (click)
- Commands: `@cli.command()` decorators in `main.py`
- Options: Use `--flag/--no-flag` for boolean toggles (e.g., `--scan-vulns/--no-scan-vulns`)
- Progress: `tqdm` for progress bars, colorama for colored terminal output

### Testing Strategy
- Unit tests: `tests/test_<module>.py` using pytest
- Integration tests: `test-scripts/` shell scripts with end-to-end validation
- Test fixtures: Place in `tests/conftest.py` for shared setup
- **Always run** `pytest -q` before committing changes

## Important Constraints

### Security Boundaries
- **Defensive Only**: Implement vulnerability detection and reporting, never exploitation capabilities
- **No Credential Harvesting**: Do not add features for bulk credential extraction or brute-forcing
- **Ethical Use**: Tools must support authorized security testing only (document this in user-facing messages)

### File Organization Rules
- Tests → `tests/` directory (NOT alongside source files)
- Scripts → `test-scripts/` or `scripts/` directory
- Reports → `output/` (gitignored, cleaned before commits)
- Documentation → Root README.md + TESTING.md + AGENTS.md (technical docs NOT in `claudedocs/`)

### Output Management
- **Never commit**: `output/` directory contents, `.env` files, local config overrides, `data/scanner.db`
- **Always generate**: Timestamped report filenames (e.g., `full_scan_20250113_120000.json`)
- **Clean before push**: Remove temporary files, test outputs, debug artifacts
- **Database files**: SQLite DB (`data/scanner.db`) is gitignored, use `setup_db.py` to recreate

## Key Workflows

### Adding New Vulnerability Checks
1. Add detection method to `VulnerabilityScanner` class (e.g., `_check_new_vuln()`)
2. Update `scan_endpoint()` to call new check method
3. Map to CWE ID and severity level (CRITICAL/HIGH/MEDIUM/LOW/INFO)
4. Add test case to `test-app/` vulnerable endpoints
5. Update documentation: README.md vulnerability table, TESTING.md expected results
6. Generate PoC template in `generate_poc()` static method

### Adding New Report Formats
1. Extend `ReportGenerator` in `src/reporter/report_generator.py`
2. Add format-specific template (Jinja2 for HTML, custom formatters for others)
3. Update `generate_all()` method to include new format
4. Add format to `config/config.yaml` default outputs
5. Document in README.md output examples section

### Modifying JavaScript Analysis Patterns
1. Update regex patterns in `JSAnalyzer.api_patterns` list
2. Test with `test-app/static/` JavaScript files
3. Verify no false positives (non-API URLs should be filtered by `_is_api_url()`)
4. Consider AST parsing enhancements in `_analyze_with_esprima()` for complex cases

## Testing Validation

### Integration Test Checklist (from TESTING.md)
After running `full-scan` on test-app:
- [ ] 10+ API endpoints discovered
- [ ] Shadow APIs detected (`/api/internal/*`, `/api/internal/debug/*`)
- [ ] 2+ CRITICAL vulnerabilities (SQL injection)
- [ ] 5+ HIGH vulnerabilities (missing auth, CORS, XSS)
- [ ] 5+ MEDIUM vulnerabilities (rate limiting, sensitive data)
- [ ] JSON + HTML + Markdown reports generated in `output/`
- [ ] Scan completes in < 60 seconds for test-app

### Manual Verification
```bash
# Test endpoint discovery
python main.py analyze test-app/static --base-url http://localhost:5000 --recursive
# Expected: 10+ endpoints including /api/internal/admin/users

# Test vulnerability detection
curl "http://localhost:5000/api/v1/user/1'"
# Expected: SQL error message → vulnerability confirmed
```

## Project-Specific Patterns

### Multi-Language Stack
- **Backend**: Python CLI (click, requests, mitmproxy)
- **Frontend**: Next.js 14 (TypeScript, React, Tailwind CSS)
- **Integration**: Web UI spawns Python processes, parses JSON output
- **Testing**: Python pytest + shell integration scripts + manual Docker validation

### Shadow API Heuristics
Endpoint flagged as "shadow" if URL contains:
- `/internal/`, `/admin/`, `/debug/`, `/test/`
- `/backup/`, `/config/`, `/secret/`, `/hidden/`, `/private/`
- `/dev/`, `/beta/`, `/v0/`, `/staging/`, `/temp/`, `/tmp/`
- Paths starting with `/_` (underscore prefix)
- Query params: `debug`, `test`, `internal`, `admin`, `dev`, `trace`, `verbose`

### Report Generation Pipeline
1. **ScanResult.finalize()**: Calculate statistics (endpoint counts, vuln severity distribution)
2. **ReportGenerator.generate_all()**: Iterate through configured formats
3. **JSON**: Direct Pydantic model serialization
4. **HTML**: Jinja2 template with styled dashboard (statistics, endpoints table, vulnerabilities)
5. **Markdown**: Text-based formatting with sections, code blocks, severity emojis

## Commit Standards

### Message Format
```
<type>: <imperative summary>

<optional body with affected modules, config changes, future work>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

**Examples**:
```
feat: add GraphQL endpoint detection in JSAnalyzer

- Extended regex patterns for graphql queries
- Added test cases in test-app/static/
- Updated TESTING.md expected endpoint count

fix: prevent false positives in CORS scanner

- Check for actual Origin header reflection
- Ignore wildcards without credentials flag
- Adjusted vulnerability severity to MEDIUM

test: add integration test for rate limiting detection

- Added burst request scenario
- Verified X-RateLimit-* header detection
- Updated test-scripts/run-test.sh validation
```

## Dependencies and Tools

### Core Python Libraries
- **mitmproxy** (10.1+): HTTP/HTTPS proxy and traffic analysis
- **requests** (2.31+): HTTP client for vulnerability testing
- **esprima** (4.0+): JavaScript AST parsing
- **beautifulsoup4** (4.12+): HTML parsing for inline scripts
- **pydantic** (2.5+): Data validation and models
- **click** (8.1+): CLI framework
- **colorama** (0.4+): Terminal colors
- **tqdm** (4.66+): Progress bars
- **jinja2** (3.1+): HTML report templating

### AI & Database (Optional)
- **openai** (1.0+): OpenAI API client for AI-powered analysis
- **python-dotenv** (1.0+): Environment variable management
- **sqlalchemy** (2.0+): Database ORM
- **psycopg2-binary** (2.9+): PostgreSQL adapter (optional)
- **alembic** (1.13+): Database migrations
- **flask** (implicit via imports): REST API server
- **flask-cors**: CORS support for web UI

### Frontend Stack
- **Next.js** 14.2: React framework with App Router
- **TypeScript** 5.3: Type safety
- **Tailwind CSS** 3.4: Utility-first styling
- **Lucide React** 0.344: Icon library
- **Axios** 1.6: HTTP client for API calls
- **Recharts** 2.12: Data visualization for statistics

## Database Architecture (src/database/)

### Database Models
**Scan Tracking** (`models.py`):
- **Scan**: Main scan record (id, target, status, progress, created_at)
- **Endpoint**: Discovered API endpoints with PoC code
- **Vulnerability**: Security findings with PoC code
- **ScanStatus Enum**: PENDING, RUNNING, COMPLETED, FAILED

**Repository Pattern** (`repository.py`):
- `create_scan()`: Initialize new scan
- `update_scan_status()`: Update progress (0-100%)
- `save_scan_result()`: Store endpoints and vulnerabilities
- `get_scan_with_details()`: Retrieve complete scan data
- `get_scan_history()`: List recent scans
- `delete_scan()`: Remove scan and related data

### Database Setup
```bash
# Initialize database (creates tables)
python setup_db.py

# Interactive prompts:
# 1. Test PostgreSQL connection (if using PostgreSQL)
# 2. Drop existing tables? (y/N)
# 3. Create new tables

# Database file location:
# SQLite: data/scanner.db (auto-created)
# PostgreSQL: Uses credentials from .env
```

**Connection Management** (`connection.py`):
- Context manager pattern: `with get_db() as db:`
- Auto-reconnection on failure
- Supports both SQLite and PostgreSQL via `DATABASE_URL`

## References

- **Main Documentation**: README.md (user guide, features, usage - in Korean)
- **Testing Guide**: TESTING.md (test scenarios, expected results, troubleshooting)
- **Agent Docs**: AGENTS.md (project guidelines for multi-agent workflows - in Korean)
- **Config Schema**: config/config.yaml (runtime settings reference)
- **Environment Template**: .env.example (configuration template for AI/DB features)
