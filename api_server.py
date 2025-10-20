"""Flask API server for Shadow API Scanner with DB integration."""

import os
import sys
import io
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import subprocess
import threading
from uuid import uuid4

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db, init_db, ScanStatus
from src.database.repository import ProjectRepository, ScanRepository
from src.utils.models import ScanResult

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()

# In-memory store for scan processes and their subprocesses
scan_processes = {}
scan_subprocesses = {}


def execute_scan_async(scan_id: str, target_url: str, js_path: str, ai_enabled: bool, bruteforce_enabled: bool, analysis_type: str, analysis_mode: str = 'both', crawl_depth: int = 1, max_pages: int = 50):
    """Execute scan asynchronously and update database."""
    try:
        print(f"\n{'='*60}", flush=True)
        print(f"[SCAN START] Scan ID: {scan_id}", flush=True)
        print(f"[SCAN START] Target: {target_url}", flush=True)
        print(f"[SCAN START] Crawl Depth: {crawl_depth}", flush=True)
        print(f"[SCAN START] Max Pages: {max_pages}", flush=True)
        print(f"{'='*60}\n", flush=True)

        # Update status to running
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.RUNNING, 10, 'Starting scan...'
            )
        print(f"[*] Database status updated to RUNNING", flush=True)

        # Get project root
        project_root = Path(__file__).parent
        output_dir = project_root / 'output' / 'web-scans' / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build command - always use full-scan to ensure --validate works
        cmd = ['python', 'main.py', 'full-scan', target_url]
        if js_path:
            cmd.extend(['--js-path', js_path])
        if bruteforce_enabled:
            cmd.append('--bruteforce')
        cmd.append('--validate')  # Always validate endpoints
        
        # Crawl depth and max pages
        cmd.extend(['--crawl-depth', str(crawl_depth)])
        cmd.extend(['--max-pages', str(max_pages)])

        # Analysis mode handling
        if analysis_mode == 'static':
            cmd.append('--static-only')
        elif analysis_mode == 'ai':
            cmd.append('--ai-only')
        elif analysis_mode == 'both':
            cmd.append('--ai')
        elif ai_enabled:
            # Backward compatibility
            cmd.append('--ai')

        cmd.extend(['--output', str(output_dir)])

        # Update progress
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.RUNNING, 30, 'Executing scanner...'
            )

        # Set environment variables
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        # Execute scan
        print(f"[*] Executing command: {' '.join(cmd)}", flush=True)
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of raising error
            env=env
        )

        # Store subprocess for potential cancellation
        scan_subprocesses[scan_id] = process
        print(f"[*] Subprocess started with PID: {process.pid}", flush=True)

        # Wait for completion with timeout and capture output
        try:
            print(f"[*] Waiting for scan {scan_id} to complete...", flush=True)
            stdout, stderr = process.communicate(timeout=900)  # 15 minutes
            returncode = process.returncode

            print(f"[*] Scan {scan_id} process completed with return code: {returncode}", flush=True)
            if stdout:
                print(f"[*] Command stdout:\n{stdout[:500]}", flush=True)  # Print first 500 chars
            if stderr:
                print(f"[*] Command stderr:\n{stderr[:500]}", flush=True)  # Print first 500 chars

            if returncode != 0:
                error_msg = f"Scan process failed with return code {returncode}\nStderr: {stderr}"
                print(f"[!] ERROR: {error_msg}", flush=True)
                raise Exception(error_msg)

        except subprocess.TimeoutExpired:
            print(f"[!] Scan {scan_id} timed out after 900 seconds", flush=True)
            process.kill()
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(cmd, 900)

        # Update progress
        print(f"[*] Updating progress to 80% - Processing results...", flush=True)
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.RUNNING, 80, 'Processing results...'
            )

        # Read JSON result
        json_files = list(output_dir.glob('*.json'))
        if not json_files:
            error_msg = f'No JSON report generated in {output_dir}'
            print(f"[!] ERROR: {error_msg}", flush=True)
            print(f"[!] Directory contents: {list(output_dir.iterdir())}", flush=True)
            raise Exception(error_msg)

        json_path = json_files[0]
        print(f"[*] Reading JSON file: {json_path}", flush=True)

        with open(json_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        # Create ScanResult object
        scan_result = ScanResult(**result_data)

        # Combine shadow_apis and public_apis into endpoints
        if not scan_result.endpoints and (result_data.get('shadow_apis') or result_data.get('public_apis')):
            from src.utils.models import APIEndpoint, HTTPMethod
            endpoints = []
            for ep_data in (result_data.get('shadow_apis', []) + result_data.get('public_apis', [])):
                ep = APIEndpoint(
                    url=ep_data['url'],
                    method=HTTPMethod[ep_data['method'].upper()],
                    parameters=ep_data.get('parameters', {}),
                    source=ep_data.get('source', 'unknown'),
                    headers=ep_data.get('headers', {}),
                    body_example=ep_data.get('body_example'),
                    response_example=ep_data.get('response_example'),
                    poc_code=ep_data.get('poc_code'),
                    status_code=ep_data.get('status_code')
                )
                endpoints.append(ep)
            scan_result.endpoints = endpoints

        # Save to database
        print(f"[*] Saving scan result to database...", flush=True)
        with get_db() as db:
            ScanRepository.save_scan_result(
                db, scan_id, scan_result, str(output_dir)
            )

        print(f"\n{'='*60}", flush=True)
        print(f"[+] Scan {scan_id} completed successfully", flush=True)
        print(f"{'='*60}\n", flush=True)

    except subprocess.TimeoutExpired:
        print(f"\n[!] Scan {scan_id} timed out", flush=True)
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.FAILED, 0, 'Scan timeout'
            )

    except Exception as e:
        print(f"\n[!] Scan {scan_id} failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.FAILED, 0, f'Scan failed: {str(e)}'
            )

    finally:
        # Remove from active processes
        print(f"[*] Cleaning up scan {scan_id}", flush=True)
        if scan_id in scan_processes:
            del scan_processes[scan_id]
        if scan_id in scan_subprocesses:
            del scan_subprocesses[scan_id]


@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start a new scan."""
    try:
        data = request.json
        target_url = data.get('target_url')
        js_path = data.get('js_path')
        project_id = data.get('project_id')
        ai_enabled = data.get('ai_enabled', True)
        bruteforce_enabled = data.get('bruteforce_enabled', False)
        analysis_type = data.get('analysis_type', 'full_scan')
        analysis_mode = data.get('analysis_mode', 'both')  # 'static', 'ai', 'both'
        crawl_depth = data.get('crawl_depth', 1)  # 크롤링 깊이 (기본값: 1)
        max_pages = data.get('max_pages', 50)  # 최대 페이지 수 (기본값: 50)

        if not target_url:
            return jsonify({'error': 'target_url is required'}), 400

        # Generate scan ID
        scan_id = str(uuid4())

        # Create scan in database
        with get_db() as db:
            ScanRepository.create_scan(
                db, scan_id, target_url, js_path, project_id,
                ai_enabled, bruteforce_enabled, analysis_type
            )

        # Start scan in background thread
        thread = threading.Thread(
            target=execute_scan_async,
            args=(scan_id, target_url, js_path, ai_enabled, bruteforce_enabled, analysis_type, analysis_mode, crawl_depth, max_pages)
        )
        thread.daemon = True
        thread.start()

        scan_processes[scan_id] = thread

        return jsonify({
            'scan_id': scan_id,
            'status': 'pending',
            'message': 'Scan started successfully'
        })

    except Exception as e:
        print(f"[!] Start scan error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to start scan', 'details': str(e)}), 500


@app.route('/api/status/<scan_id>', methods=['GET'])
def get_scan_status(scan_id):
    """Get scan status."""
    try:
        with get_db() as db:
            result = ScanRepository.get_scan_with_details(db, scan_id)

        if not result:
            return jsonify({'error': 'Scan not found'}), 404

        # discovered_paths are now loaded directly from database
        response = jsonify(result)

        # Prevent caching for real-time status updates
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        print(f"[!] Get status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get scan status', 'details': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_scan_history():
    """Get scan history."""
    try:
        limit = request.args.get('limit', 10, type=int)

        with get_db() as db:
            scans = ScanRepository.get_scan_history(db, limit=limit)

        return jsonify({'scans': scans})

    except Exception as e:
        print(f"[!] Get history error: {e}")
        return jsonify({'error': 'Failed to get scan history', 'details': str(e)}), 500


@app.route('/api/scan/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    """Delete a scan."""
    try:
        with get_db() as db:
            success = ScanRepository.delete_scan(db, scan_id)

        if success:
            return jsonify({'message': 'Scan deleted successfully'})
        else:
            return jsonify({'error': 'Scan not found'}), 404

    except Exception as e:
        print(f"[!] Delete scan error: {e}")
        return jsonify({'error': 'Failed to delete scan', 'details': str(e)}), 500


@app.route('/api/scan/<scan_id>/stop', methods=['POST'])
def stop_scan(scan_id):
    """Stop a running scan."""
    try:
        # Check if scan is running
        if scan_id not in scan_subprocesses:
            return jsonify({'error': 'Scan is not running or already completed'}), 404

        # Kill the subprocess
        process = scan_subprocesses[scan_id]
        if process and process.poll() is None:  # Process is still running
            print(f"[*] Stopping scan {scan_id}...")
            process.kill()
            process.wait()  # Wait for process to terminate

        # Update database status
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.FAILED, 0, 'Scan stopped by user'
            )

        # Clean up
        if scan_id in scan_processes:
            del scan_processes[scan_id]
        if scan_id in scan_subprocesses:
            del scan_subprocesses[scan_id]

        print(f"[+] Scan {scan_id} stopped successfully")
        return jsonify({
            'message': 'Scan stopped successfully',
            'scan_id': scan_id
        })

    except Exception as e:
        print(f"[!] Stop scan error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to stop scan', 'details': str(e)}), 500


@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    try:
        with get_db() as db:
            projects = ProjectRepository.get_all_projects(db)
            return jsonify({
                'projects': [p.to_dict() for p in projects]
            })
    except Exception as e:
        print(f"[!] Get projects error: {e}")
        return jsonify({'error': 'Failed to get projects', 'details': str(e)}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({'error': 'name is required'}), 400

        with get_db() as db:
            project = ProjectRepository.create_project(db, name, description)
            return jsonify({
                'project': project.to_dict(),
                'message': 'Project created successfully'
            })
    except Exception as e:
        print(f"[!] Create project error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create project', 'details': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details with scans."""
    try:
        with get_db() as db:
            project = ProjectRepository.get_project_with_scans(db, project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            return jsonify(project)
    except Exception as e:
        print(f"[!] Get project error: {e}")
        return jsonify({'error': 'Failed to get project', 'details': str(e)}), 500


@app.route('/api/projects/<project_id>/statistics', methods=['GET'])
def get_project_statistics(project_id):
    """Get comprehensive statistics for a project."""
    try:
        with get_db() as db:
            from src.database.models import Scan as ScanModel, Endpoint as EndpointModel, Vulnerability as VulnModel, Project as ProjectModel
            from sqlalchemy import func
            
            # Get project by UUID
            project = db.query(ProjectModel).filter(ProjectModel.project_id == project_id).first()
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            # Get all scans for this project using the integer ID
            scans = db.query(ScanModel).filter(ScanModel.project_id == project.id).all()
            
            # Total scans
            total_scans = len(scans)
            completed_scans = len([s for s in scans if str(s.status).endswith('COMPLETED')])
            failed_scans = len([s for s in scans if str(s.status).endswith('FAILED')])
            
            # Get all endpoints from completed scans
            scan_ids = [s.id for s in scans if str(s.status).endswith('COMPLETED')]
            endpoints = db.query(EndpointModel).filter(EndpointModel.scan_id.in_(scan_ids)).all() if scan_ids else []
            
            # Endpoint statistics
            total_endpoints = len(endpoints)
            shadow_apis = len([e for e in endpoints if e.is_shadow_api])
            public_apis = len([e for e in endpoints if not e.is_shadow_api])
            
            # Status code distribution
            count_2xx = len([e for e in endpoints if e.status_code and 200 <= e.status_code < 300])
            count_3xx = len([e for e in endpoints if e.status_code and 300 <= e.status_code < 400])
            count_4xx = len([e for e in endpoints if e.status_code and 400 <= e.status_code < 500])
            count_5xx = len([e for e in endpoints if e.status_code and 500 <= e.status_code < 600])
            
            # Method distribution
            method_counts = {}
            for ep in endpoints:
                method_counts[ep.method] = method_counts.get(ep.method, 0) + 1
            
            # Get all vulnerabilities
            vulnerabilities = db.query(VulnModel).filter(VulnModel.scan_id.in_(scan_ids)).all() if scan_ids else []
            
            # Vulnerability statistics
            total_vulns = len(vulnerabilities)
            vuln_by_severity = {
                'critical': len([v for v in vulnerabilities if str(v.level).endswith('CRITICAL')]),
                'high': len([v for v in vulnerabilities if str(v.level).endswith('HIGH')]),
                'medium': len([v for v in vulnerabilities if str(v.level).endswith('MEDIUM')]),
                'low': len([v for v in vulnerabilities if str(v.level).endswith('LOW')]),
                'info': len([v for v in vulnerabilities if str(v.level).endswith('INFO')])
            }
            
            # Vulnerability types
            vuln_types = {}
            for v in vulnerabilities:
                vuln_types[v.type] = vuln_types.get(v.type, 0) + 1
            
            # Recent scan activity (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Helper function to parse datetime
            def parse_datetime(dt):
                if isinstance(dt, datetime):
                    return dt
                elif isinstance(dt, str):
                    return datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return datetime.now()
            
            recent_scans = [s for s in scans if parse_datetime(s.created_at) > thirty_days_ago]
            
            # Timeline data - scans per day for last 30 days
            timeline_data = {}
            for scan in recent_scans:
                scan_date = parse_datetime(scan.created_at).date()
                date_str = scan_date.isoformat()
                if date_str not in timeline_data:
                    timeline_data[date_str] = {'scans': 0, 'endpoints': 0, 'vulnerabilities': 0}
                timeline_data[date_str]['scans'] += 1
                
                # Count endpoints and vulns for this scan
                scan_endpoints = [e for e in endpoints if e.scan_id == scan.id]
                scan_vulns = [v for v in vulnerabilities if v.scan_id == scan.id]
                timeline_data[date_str]['endpoints'] += len(scan_endpoints)
                timeline_data[date_str]['vulnerabilities'] += len(scan_vulns)
            
            # Convert timeline to sorted list
            timeline = [
                {'date': date, **data} 
                for date, data in sorted(timeline_data.items())
            ]
            
            # Top vulnerable endpoints
            endpoint_vuln_counts = {}
            for vuln in vulnerabilities:
                endpoint_vuln_counts[vuln.endpoint] = endpoint_vuln_counts.get(vuln.endpoint, 0) + 1
            
            top_vulnerable_endpoints = sorted(
                [{'endpoint': ep, 'count': count} for ep, count in endpoint_vuln_counts.items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10]
            
            # Success rate
            success_rate = (completed_scans / total_scans * 100) if total_scans > 0 else 0
            
            return jsonify({
                'project': project.to_dict(),
                'overview': {
                    'total_scans': total_scans,
                    'completed_scans': completed_scans,
                    'failed_scans': failed_scans,
                    'success_rate': round(success_rate, 1),
                    'total_endpoints': total_endpoints,
                    'shadow_apis': shadow_apis,
                    'public_apis': public_apis,
                    'total_vulnerabilities': total_vulns,
                    'count_2xx': count_2xx,
                    'count_3xx': count_3xx,
                    'count_4xx': count_4xx,
                    'count_5xx': count_5xx
                },
                'vulnerabilities': {
                    'by_severity': vuln_by_severity,
                    'by_type': vuln_types,
                    'top_vulnerable_endpoints': top_vulnerable_endpoints
                },
                'endpoints': {
                    'by_method': method_counts,
                    'shadow_ratio': round((shadow_apis / total_endpoints * 100) if total_endpoints > 0 else 0, 1),
                    'by_status_code': {
                        '2xx': count_2xx,
                        '3xx': count_3xx,
                        '4xx': count_4xx,
                        '5xx': count_5xx
                    }
                },
                'timeline': timeline,
                'recent_activity': {
                    'scans_last_30_days': len(recent_scans),
                    'last_scan': scans[-1].created_at.isoformat() if scans and hasattr(scans[-1].created_at, 'isoformat') else (scans[-1].created_at if scans else None)
                }
            })
            
    except Exception as e:
        print(f"[!] Get project statistics error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get project statistics', 'details': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project information."""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')

        with get_db() as db:
            project = ProjectRepository.update_project(db, project_id, name, description)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            return jsonify({
                'project': project.to_dict(),
                'message': 'Project updated successfully'
            })
    except Exception as e:
        print(f"[!] Update project error: {e}")
        return jsonify({'error': 'Failed to update project', 'details': str(e)}), 500


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and all its scans."""
    try:
        with get_db() as db:
            success = ProjectRepository.delete_project(db, project_id)
            if success:
                return jsonify({'message': 'Project deleted successfully'})
            else:
                return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        print(f"[!] Delete project error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to delete project', 'details': str(e)}), 500


@app.route('/api/vulnerability/<vuln_id>/generate-poc', methods=['POST'])
def generate_vulnerability_poc(vuln_id):
    """PoC generation is no longer supported."""
    return jsonify({
        'error': 'PoC generation feature has been removed',
        'details': 'AI-based PoC generation is no longer available'
    }), 503


@app.route('/api/scan/<scan_id>/generate-all-pocs', methods=['POST'])
def generate_all_pocs_for_scan(scan_id):
    """PoC generation is no longer supported."""
    return jsonify({
        'error': 'PoC generation feature has been removed',
        'details': 'AI-based PoC generation is no longer available'
    }), 503


@app.route('/api/endpoint/<int:endpoint_id>/http-request', methods=['GET'])
def generate_single_http_request(endpoint_id):
    """Generate .http/.req file for a single endpoint."""
    try:
        format_type = request.args.get('format', 'http')  # http, burp
        
        with get_db() as db:
            from src.database.models import Endpoint
            endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
            if not endpoint:
                return jsonify({'error': 'Endpoint not found'}), 404
            
            # Get scan info for base URL
            scan = ScanRepository.get_scan_by_id(db, endpoint.scan_id)
            target_url = scan.target_url if scan else 'http://localhost'
            
            # Parse URL
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            host = parsed.netloc or 'localhost:5000'
            scheme = parsed.scheme or 'http'
            
            url = endpoint.url
            if not url.startswith('http'):
                full_url = f"{target_url}{url}"
            else:
                full_url = url
            
            # Generate Burp Suite format (Raw HTTP)
            if format_type == 'burp':
                burp_content = f"{endpoint.method} {url} HTTP/1.1\r\n"
                burp_content += f"Host: {host}\r\n"
                
                # Add headers
                default_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                }
                
                added_headers = set()
                
                # Add captured headers first
                if endpoint.request_headers:
                    try:
                        headers = json.loads(endpoint.request_headers) if isinstance(endpoint.request_headers, str) else endpoint.request_headers
                        for key, value in headers.items():
                            if key.lower() not in ['host', 'content-length']:
                                burp_content += f"{key}: {value}\r\n"
                                added_headers.add(key.lower())
                    except Exception as e:
                        print(f"[!] Error parsing headers: {e}")
                
                # Add default headers if not already present
                for key, value in default_headers.items():
                    if key.lower() not in added_headers:
                        burp_content += f"{key}: {value}\r\n"
                
                # Add Content-Type for POST/PUT/PATCH if not present
                if endpoint.method in ['POST', 'PUT', 'PATCH']:
                    if 'content-type' not in added_headers:
                        burp_content += "Content-Type: application/json\r\n"
                    
                    # Get body content
                    if endpoint.request_body:
                        try:
                            # If it's a JSON string, parse and re-format it nicely
                            if isinstance(endpoint.request_body, str):
                                try:
                                    body_obj = json.loads(endpoint.request_body)
                                    body = json.dumps(body_obj, indent=2)
                                except:
                                    body = endpoint.request_body
                            else:
                                body = json.dumps(endpoint.request_body, indent=2)
                        except:
                            body = str(endpoint.request_body)
                    elif endpoint.parameters:
                        # Use parameters from JS analysis
                        try:
                            params = json.loads(endpoint.parameters) if isinstance(endpoint.parameters, str) else endpoint.parameters
                            body_obj = {}
                            
                            for key, value in params.items():
                                # Generate appropriate values based on parameter name
                                key_lower = key.lower()
                                if any(x in key_lower for x in ['user', 'username', 'login']):
                                    body_obj[key] = "admin"
                                elif any(x in key_lower for x in ['pass', 'password', 'pwd']):
                                    body_obj[key] = "password123"
                                elif any(x in key_lower for x in ['email', 'mail']):
                                    body_obj[key] = "user@example.com"
                                elif any(x in key_lower for x in ['name', 'fullname', 'firstname']):
                                    body_obj[key] = "John Doe"
                                elif any(x in key_lower for x in ['phone', 'tel', 'mobile']):
                                    body_obj[key] = "010-1234-5678"
                                elif any(x in key_lower for x in ['token', 'key', 'apikey']):
                                    body_obj[key] = "your_token_here"
                                elif any(x in key_lower for x in ['id', 'userid', 'user_id']):
                                    body_obj[key] = 1
                                elif any(x in key_lower for x in ['count', 'limit', 'size', 'page']):
                                    body_obj[key] = 10
                                elif any(x in key_lower for x in ['enable', 'active', 'is_']):
                                    body_obj[key] = True
                                elif isinstance(value, str):
                                    body_obj[key] = value if value else "example_value"
                                elif isinstance(value, bool):
                                    body_obj[key] = True
                                elif isinstance(value, (int, float)):
                                    body_obj[key] = value if value else 0
                                else:
                                    body_obj[key] = str(value) if value else "value"
                            
                            body = json.dumps(body_obj, indent=2)
                        except Exception as e:
                            print(f"[!] Error generating body from parameters: {e}")
                            # Fallback to URL-based generation
                            if 'login' in url.lower() or 'auth' in url.lower():
                                body = json.dumps({
                                    "username": "admin",
                                    "password": "password123"
                                }, indent=2)
                            elif 'register' in url.lower() or 'signup' in url.lower():
                                body = json.dumps({
                                    "username": "newuser",
                                    "email": "user@example.com",
                                    "password": "password123"
                                }, indent=2)
                            else:
                                body = json.dumps({
                                    "key": "value",
                                    "data": "example"
                                }, indent=2)
                    else:
                        # Generate example body based on common patterns
                        if 'login' in url.lower() or 'auth' in url.lower():
                            body = json.dumps({
                                "username": "admin",
                                "password": "password123"
                            }, indent=2)
                        elif 'register' in url.lower() or 'signup' in url.lower():
                            body = json.dumps({
                                "username": "newuser",
                                "email": "user@example.com",
                                "password": "password123"
                            }, indent=2)
                        elif 'user' in url.lower():
                            body = json.dumps({
                                "name": "John Doe",
                                "email": "john@example.com",
                                "role": "user"
                            }, indent=2)
                        else:
                            body = json.dumps({
                                "key": "value",
                                "data": "example"
                            }, indent=2)
                    
                    burp_content += f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                    burp_content += "\r\n"
                    burp_content += body
                else:
                    burp_content += "\r\n"
                
                safe_url = url.replace('/', '_').replace(':', '').replace('?', '_').replace('&', '_')[:50]
                filename = f"{endpoint.method}_{safe_url}_burp.txt"
                
                return jsonify({
                    'success': True,
                    'content': burp_content,
                    'filename': filename,
                    'format': 'burp'
                })
            
            # Generate .http/.req content (default)
            else:
                http_content = f"""### Shadow API Scanner - Single Endpoint
### Endpoint ID: {endpoint.id}
### Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### ============================================================
### Variables
### ============================================================
@baseUrl = {target_url}

### ============================================================
### {endpoint.method} {endpoint.url}
### ============================================================

"""
                
                # Clean URL
                if not url.startswith('http'):
                    full_url_var = f"{{{{baseUrl}}}}{url}"
                else:
                    full_url_var = url
                
                # Add comment with status code
                http_content += f"### {endpoint.method} {url}\n"
                http_content += f"# Status: {endpoint.status_code}\n"
                
                # Add Response Time if available
                if endpoint.response_time:
                    http_content += f"# Response Time: {endpoint.response_time}ms\n"
                
                # Add request
                http_content += f"{endpoint.method} {full_url_var}\n"
                
                # Add headers
                added_headers = set()
                if endpoint.request_headers:
                    try:
                        headers = json.loads(endpoint.request_headers) if isinstance(endpoint.request_headers, str) else endpoint.request_headers
                        for key, value in headers.items():
                            if key.lower() not in ['host', 'content-length']:
                                http_content += f"{key}: {value}\n"
                                added_headers.add(key.lower())
                    except Exception as e:
                        print(f"[!] Error parsing headers: {e}")
                
                # Add default headers if not present
                if 'user-agent' not in added_headers:
                    http_content += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n"
                if 'accept' not in added_headers:
                    http_content += "Accept: application/json, text/plain, */*\n"
                
                # Add body for POST/PUT/PATCH
                if endpoint.method in ['POST', 'PUT', 'PATCH']:
                    if 'content-type' not in added_headers:
                        http_content += "Content-Type: application/json\n"
                    
                    http_content += "\n"
                    
                    if endpoint.request_body:
                        try:
                            # If it's a JSON string, parse and re-format it nicely
                            if isinstance(endpoint.request_body, str):
                                try:
                                    body_obj = json.loads(endpoint.request_body)
                                    http_content += json.dumps(body_obj, indent=2) + "\n"
                                except:
                                    http_content += endpoint.request_body + "\n"
                            else:
                                http_content += json.dumps(endpoint.request_body, indent=2) + "\n"
                        except:
                            http_content += str(endpoint.request_body) + "\n"
                    elif endpoint.parameters:
                        # Use parameters from JS analysis
                        try:
                            params = json.loads(endpoint.parameters) if isinstance(endpoint.parameters, str) else endpoint.parameters
                            body_obj = {}
                            
                            for key, value in params.items():
                                # Generate appropriate values based on parameter name
                                key_lower = key.lower()
                                if any(x in key_lower for x in ['user', 'username', 'login']):
                                    body_obj[key] = "admin"
                                elif any(x in key_lower for x in ['pass', 'password', 'pwd']):
                                    body_obj[key] = "password123"
                                elif any(x in key_lower for x in ['email', 'mail']):
                                    body_obj[key] = "user@example.com"
                                elif any(x in key_lower for x in ['name', 'fullname', 'firstname']):
                                    body_obj[key] = "John Doe"
                                elif any(x in key_lower for x in ['phone', 'tel', 'mobile']):
                                    body_obj[key] = "010-1234-5678"
                                elif any(x in key_lower for x in ['token', 'key', 'apikey']):
                                    body_obj[key] = "your_token_here"
                                elif any(x in key_lower for x in ['id', 'userid', 'user_id']):
                                    body_obj[key] = 1
                                elif any(x in key_lower for x in ['count', 'limit', 'size', 'page']):
                                    body_obj[key] = 10
                                elif any(x in key_lower for x in ['enable', 'active', 'is_']):
                                    body_obj[key] = True
                                elif isinstance(value, str):
                                    body_obj[key] = value if value else "example_value"
                                elif isinstance(value, bool):
                                    body_obj[key] = True
                                elif isinstance(value, (int, float)):
                                    body_obj[key] = value if value else 0
                                else:
                                    body_obj[key] = str(value) if value else "value"
                            
                            http_content += json.dumps(body_obj, indent=2) + "\n"
                        except Exception as e:
                            print(f"[!] Error generating body from parameters: {e}")
                            # Fallback to URL-based generation
                            if 'login' in url.lower() or 'auth' in url.lower():
                                http_content += json.dumps({
                                    "username": "admin",
                                    "password": "password123"
                                }, indent=2) + "\n"
                            elif 'register' in url.lower() or 'signup' in url.lower():
                                http_content += json.dumps({
                                    "username": "newuser",
                                    "email": "user@example.com",
                                    "password": "password123"
                                }, indent=2) + "\n"
                            else:
                                http_content += json.dumps({
                                    "key": "value",
                                    "data": "example"
                                }, indent=2) + "\n"
                    else:
                        # Generate example body based on common patterns
                        if 'login' in url.lower() or 'auth' in url.lower():
                            http_content += json.dumps({
                                "username": "admin",
                                "password": "password123"
                            }, indent=2) + "\n"
                        elif 'register' in url.lower() or 'signup' in url.lower():
                            http_content += json.dumps({
                                "username": "newuser",
                                "email": "user@example.com",
                                "password": "password123"
                            }, indent=2) + "\n"
                        elif 'user' in url.lower():
                            http_content += json.dumps({
                                "name": "John Doe",
                                "email": "john@example.com",
                                "role": "user"
                            }, indent=2) + "\n"
                        else:
                            http_content += json.dumps({
                                "key": "value",
                                "data": "example"
                            }, indent=2) + "\n"
                
                http_content += "\n###\n"
                
                # Add response info if available
                if endpoint.response_headers or endpoint.response_body:
                    http_content += "\n### Expected Response\n"
                    if endpoint.response_headers:
                        try:
                            resp_headers = json.loads(endpoint.response_headers) if isinstance(endpoint.response_headers, str) else endpoint.response_headers
                            http_content += "# Response Headers:\n"
                            for key, value in resp_headers.items():
                                http_content += f"#   {key}: {value}\n"
                        except:
                            pass
                    
                    if endpoint.response_body:
                        http_content += "\n# Response Body:\n"
                        try:
                            if isinstance(endpoint.response_body, str):
                                try:
                                    resp_obj = json.loads(endpoint.response_body)
                                    formatted = json.dumps(resp_obj, indent=2)
                                    for line in formatted.split('\n'):
                                        http_content += f"# {line}\n"
                                except:
                                    for line in endpoint.response_body.split('\n')[:20]:  # Limit to 20 lines
                                        http_content += f"# {line}\n"
                            else:
                                formatted = json.dumps(endpoint.response_body, indent=2)
                                for line in formatted.split('\n'):
                                    http_content += f"# {line}\n"
                        except:
                            pass
                
                # Generate filename
                safe_url = url.replace('/', '_').replace(':', '').replace('?', '_').replace('&', '_')[:50]
                filename = f"{endpoint.method}_{safe_url}.http"
                
                return jsonify({
                    'success': True,
                    'content': http_content,
                    'filename': filename,
                    'format': 'http'
                })
            
    except Exception as e:
        print(f"[!] Error generating HTTP request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan/<scan_id>/endpoints/curl-all', methods=['GET'])
def generate_all_curl_commands(scan_id):
    """Curl generation is no longer supported."""
    return jsonify({
        'error': 'Curl generation feature has been removed',
        'details': 'Curl command generation is no longer available'
    }), 503


@app.route('/api/scan/<scan_id>/postman-collection', methods=['GET'])
def generate_postman_collection(scan_id):
    """Postman collection generation is no longer supported."""
    return jsonify({
        'error': 'Postman collection generation feature has been removed',
        'details': 'Postman collection generation is no longer available'
    }), 503


@app.route('/api/scan/<scan_id>/http-requests', methods=['GET'])
def generate_http_requests(scan_id):
    """Generate .http/.req file for REST Client from scan endpoints."""
    try:
        format_type = request.args.get('format', 'http')  # http, burp
        
        with get_db() as db:
            scan = ScanRepository.get_scan_by_id(db, scan_id)
            if not scan:
                return jsonify({'error': 'Scan not found'}), 404
            
            endpoints = ScanRepository.get_endpoints_by_scan_id(db, scan_id)
            if not endpoints:
                return jsonify({'error': 'No endpoints found'}), 404
            
            target_url = scan.target_url
            
            # Parse URL for Burp format
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            host = parsed.netloc or 'localhost:5000'
            scheme = parsed.scheme or 'http'
            
            # Generate Burp Suite format (Raw HTTP - multiple requests)
            if format_type == 'burp':
                burp_content = f"""# Shadow API Scanner - Burp Suite Raw HTTP Requests
# Generated from Scan ID: {scan_id}
# Target: {target_url}
# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# Instructions:
# 1. Copy each request block (between ===== separators)
# 2. Paste into Burp Suite Repeater tab
# 3. Modify and send as needed
#
# ============================================================

"""
                
                # Group endpoints by method
                endpoints_by_method = {}
                for endpoint in endpoints:
                    method = endpoint.method
                    if method not in endpoints_by_method:
                        endpoints_by_method[method] = []
                    endpoints_by_method[method].append(endpoint)
                
                # Generate raw HTTP requests
                for method in sorted(endpoints_by_method.keys()):
                    burp_content += f"\n# ============ {method} Requests ============\n\n"
                    
                    for endpoint in endpoints_by_method[method]:
                        url = endpoint.url
                        
                        burp_content += f"# {method} {url} (Status: {endpoint.status_code})\n"
                        burp_content += "# " + "="*60 + "\n"
                        
                        # Request line
                        burp_content += f"{method} {url} HTTP/1.1\r\n"
                        burp_content += f"Host: {host}\r\n"
                        
                        # Headers
                        if endpoint.request_headers:
                            try:
                                headers = json.loads(endpoint.request_headers) if isinstance(endpoint.request_headers, str) else endpoint.request_headers
                                for key, value in headers.items():
                                    if key.lower() not in ['host', 'content-length', 'connection']:
                                        burp_content += f"{key}: {value}\r\n"
                            except:
                                pass
                        
                        # Content-Type and Body for POST/PUT/PATCH
                        if method in ['POST', 'PUT', 'PATCH']:
                            has_content_type = False
                            if endpoint.request_headers:
                                try:
                                    headers = json.loads(endpoint.request_headers) if isinstance(endpoint.request_headers, str) else endpoint.request_headers
                                    has_content_type = any(k.lower() == 'content-type' for k in headers.keys())
                                except:
                                    pass
                            
                            if not has_content_type:
                                burp_content += "Content-Type: application/json\r\n"
                            
                            body = endpoint.request_body if endpoint.request_body else '{"key": "value"}'
                            burp_content += f"Content-Length: {len(body)}\r\n"
                            burp_content += "\r\n"
                            burp_content += body
                        else:
                            burp_content += "\r\n"
                        
                        burp_content += "\n\n# " + "="*60 + "\n\n"
                
                return jsonify({
                    'success': True,
                    'content': burp_content,
                    'filename': f'scan_{scan_id}_burp.txt',
                    'format': 'burp'
                })
            
            # Generate .http/.req content (default)
            else:
                http_content = f"""### Shadow API Scanner - Scan Results
### Generated from Scan ID: {scan_id}
### Target: {target_url}
### Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### ============================================================
### Variables
### ============================================================
@baseUrl = {target_url}

### ============================================================
### Discovered Endpoints
### ============================================================

"""
                
                # Group endpoints by method
                endpoints_by_method = {}
                for endpoint in endpoints:
                    method = endpoint.method
                    if method not in endpoints_by_method:
                        endpoints_by_method[method] = []
                    endpoints_by_method[method].append(endpoint)
                
                # Generate requests for each method group
                for method in sorted(endpoints_by_method.keys()):
                    http_content += f"\n### {method} Requests\n###\n\n"
                    
                    for endpoint in endpoints_by_method[method]:
                        url = endpoint.url
                        # Clean URL
                        if not url.startswith('http'):
                            full_url = f"{{{{baseUrl}}}}{url}"
                        else:
                            full_url = url
                        
                        # Add comment with status code
                        http_content += f"### {method} {url}\n"
                        http_content += f"# Status: {endpoint.status_code}\n"
                        
                        # Add request
                        http_content += f"{method} {full_url}\n"
                        
                        # Add headers if available
                        if endpoint.request_headers:
                            try:
                                headers = json.loads(endpoint.request_headers) if isinstance(endpoint.request_headers, str) else endpoint.request_headers
                                for key, value in headers.items():
                                    if key.lower() not in ['host', 'content-length', 'connection']:
                                        http_content += f"{key}: {value}\n"
                            except:
                                pass
                        
                        # Add body for POST/PUT/PATCH
                        if method in ['POST', 'PUT', 'PATCH']:
                            http_content += "Content-Type: application/json\n\n"
                            if endpoint.request_body:
                                http_content += f"{endpoint.request_body}\n"
                            else:
                                http_content += '{\n  "key": "value"\n}\n'
                        
                        http_content += "\n###\n\n"
                
                return jsonify({
                    'success': True,
                    'content': http_content,
                    'filename': f'scan_{scan_id}.http',
                    'format': 'http'
                })
            
    except Exception as e:
        print(f"[!] Error generating HTTP requests: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'API server is running'})


@app.route('/api/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint for discussing scan results."""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        scan_context = data.get('scan_context', {})
        conversation_history = data.get('conversation_history', [])

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Check if OpenAI API key is available
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'response': '죄송합니다. AI 챗 기능을 사용하려면 OpenAI API 키가 필요합니다. 환경 변수 OPENAI_API_KEY를 설정해주세요.'
            })

        # Import OpenAI
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
        except ImportError:
            return jsonify({
                'response': 'OpenAI 라이브러리가 설치되지 않았습니다. `pip install openai`를 실행해주세요.'
            })

        # Prepare enhanced system message with comprehensive scan context
        stats = scan_context.get('statistics', {})
        endpoint_samples = scan_context.get('endpoint_samples', {})
        methods_dist = scan_context.get('methods_distribution', {})
        
        # Format endpoint samples for context with detailed request/response data
        samples_text = ""
        detailed_samples = []
        
        if endpoint_samples:
            by_status = endpoint_samples.get('by_status', {})
            sensitive = endpoint_samples.get('sensitive_endpoints', [])
            
            # Add detailed samples with request/response data
            for status_type, endpoints in by_status.items():
                for ep in endpoints[:2]:  # Top 2 per status type
                    ep_detail = f"\n[{ep.get('method', 'GET')} {ep.get('url', '')}]"
                    if ep.get('status_code'):
                        ep_detail += f" → {ep.get('status_code')}"
                    if ep.get('response_time'):
                        ep_detail += f" ({ep.get('response_time')}ms)"
                    if ep.get('request_body'):
                        body_preview = ep.get('request_body', '')[:100]
                        ep_detail += f"\n  요청: {body_preview}..."
                    if ep.get('response_body'):
                        resp_preview = ep.get('response_body', '')[:150]
                        ep_detail += f"\n  응답: {resp_preview}..."
                    detailed_samples.append(ep_detail)
            
            # Add URL-only summaries
            if by_status.get('success_2xx'):
                samples_text += f"\n성공(2xx): {len(by_status['success_2xx'])}개"
            if by_status.get('client_error_4xx'):
                samples_text += f"\n클라이언트 에러(4xx): {len(by_status['client_error_4xx'])}개"
            if by_status.get('server_error_5xx'):
                samples_text += f"\n서버 에러(5xx): {len(by_status['server_error_5xx'])}개"
            if sensitive:
                samples_text += f"\n⚠️ 민감 엔드포인트: {', '.join([ep.get('url', '') for ep in sensitive[:3]])}"
        
        # Combine detailed samples
        if detailed_samples:
            samples_text += "\n\n📋 상세 예시:" + "".join(detailed_samples[:5])
        
        methods_text = f"GET:{methods_dist.get('GET',0)} POST:{methods_dist.get('POST',0)} PUT:{methods_dist.get('PUT',0)} DELETE:{methods_dist.get('DELETE',0)}" if methods_dist else ""
        
        system_message = f"""당신은 API 보안 전문가입니다. 실제 HTTP 트래픽 데이터를 기반으로 구체적이고 실용적인 분석을 제공하세요.

📊 스캔 결과:
- URL: {scan_context.get('target_url', 'N/A')}
- 엔드포인트: {scan_context.get('total_endpoints', 0)}개
- 상태: 2xx({stats.get('count_2xx', 0)}) 3xx({stats.get('count_3xx', 0)}) 4xx({stats.get('count_4xx', 0)}) 5xx({stats.get('count_5xx', 0)})
- HTTP 메서드: {methods_text}
- 발견 경로: {scan_context.get('discovered_paths_count', 0)}개{samples_text}

📋 분석 가이드:
1. 실제 요청/응답 데이터에서 보안 취약점 식별
2. 요청 body에서 민감 정보 노출 확인
3. 응답 데이터에서 정보 유출 위험 평가
4. HTTP 헤더 보안 설정 점검
5. 응답 시간으로 성능 이슈 파악
6. 구체적인 개선 권장사항 제공

위의 상세 예시에 있는 실제 요청/응답 내용을 참조하여 답변하세요."""

        # Prepare messages for OpenAI (optimized - only last 4 messages for faster response)
        messages = [
            {"role": "system", "content": system_message}
        ]

        # Add conversation history (last 4 messages only for performance)
        for msg in conversation_history[-4:]:
            if msg.get('content'):  # Skip empty messages
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call OpenAI API (optimized with GPT-3.5-turbo for faster response)
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Faster and cheaper than GPT-4
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused, accurate responses
                max_tokens=1000,  # Increased for more detailed analysis
                timeout=30  # 30 second timeout
            )

            assistant_message = response.choices[0].message.content

            return jsonify({
                'response': assistant_message,
                'model': 'gpt-3.5-turbo'
            })

        except Exception as e:
            error_str = str(e)
            print(f"[!] OpenAI API error: {error_str}")
            
            # Handle specific error types
            if 'authentication' in error_str.lower() or 'api key' in error_str.lower():
                return jsonify({
                    'response': 'OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.'
                })
            elif 'rate limit' in error_str.lower() or 'quota' in error_str.lower():
                return jsonify({
                    'response': 'OpenAI API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.'
                })
            else:
                return jsonify({
                    'response': f'AI 응답 생성 중 오류가 발생했습니다: {error_str}'
                })

    except Exception as e:
        print(f"[!] Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to process chat message', 'details': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Shadow API Scanner - API Server")
    print("="*60)
    print(f"Server starting on http://localhost:5001")
    print(f"Database: SQLite - {Path(__file__).parent / 'data' / 'scanner.db'}")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
