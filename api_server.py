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


def execute_scan_async(scan_id: str, target_url: str, js_path: str, scan_vulns: bool, ai_enabled: bool, bruteforce_enabled: bool, analysis_type: str):
    """Execute scan asynchronously and update database."""
    try:
        # Update status to running
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.RUNNING, 10, 'Starting scan...'
            )

        # Get project root
        project_root = Path(__file__).parent
        output_dir = project_root / 'output' / 'web-scans' / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build command
        if analysis_type == 'js_only' and js_path:
            cmd = [
                'python', 'main.py', 'analyze', js_path,
                '--base-url', target_url
            ]
        else:
            cmd = ['python', 'main.py', 'full-scan', target_url]
            if js_path:
                cmd.extend(['--js-path', js_path])
            if scan_vulns:
                cmd.append('--scan-vulns')
            else:
                cmd.append('--no-scan-vulns')
            if bruteforce_enabled:
                cmd.append('--bruteforce')
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
        env['AI_ANALYSIS_ENABLED'] = 'true' if ai_enabled else 'false'

        # Execute scan
        print(f"[*] Executing command: {' '.join(cmd)}")
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

        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=900)  # 15 minutes
            result = type('obj', (object,), {'stdout': stdout, 'stderr': stderr, 'returncode': process.returncode})()
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(cmd, 900)

        print(f"[*] Command stdout: {result.stdout}")
        if result.stderr:
            print(f"[*] Command stderr: {result.stderr}")

        # Update progress
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.RUNNING, 80, 'Processing results...'
            )

        # Read JSON result
        json_files = list(output_dir.glob('*.json'))
        if not json_files:
            raise Exception('No JSON report generated')

        json_path = json_files[0]
        print(f"[*] Reading JSON file: {json_path}")

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
                    poc_code=ep_data.get('poc_code')
                )
                endpoints.append(ep)
            scan_result.endpoints = endpoints

        # Save to database
        with get_db() as db:
            ScanRepository.save_scan_result(
                db, scan_id, scan_result, str(output_dir)
            )

        print(f"[+] Scan {scan_id} completed successfully")

    except subprocess.TimeoutExpired:
        print(f"[!] Scan {scan_id} timed out")
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.FAILED, 0, 'Scan timeout'
            )

    except Exception as e:
        print(f"[!] Scan {scan_id} failed: {e}")
        import traceback
        traceback.print_exc()
        with get_db() as db:
            ScanRepository.update_scan_status(
                db, scan_id, ScanStatus.FAILED, 0, f'Scan failed: {str(e)}'
            )

    finally:
        # Remove from active processes
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
        scan_vulns = data.get('scan_vulns', True)
        ai_enabled = data.get('ai_enabled', True)
        bruteforce_enabled = data.get('bruteforce_enabled', False)
        analysis_type = data.get('analysis_type', 'full_scan')

        if not target_url:
            return jsonify({'error': 'target_url is required'}), 400

        # Generate scan ID
        scan_id = str(uuid4())

        # Create scan in database
        with get_db() as db:
            ScanRepository.create_scan(
                db, scan_id, target_url, js_path, project_id,
                scan_vulns, ai_enabled, bruteforce_enabled, analysis_type
            )

        # Start scan in background thread
        thread = threading.Thread(
            target=execute_scan_async,
            args=(scan_id, target_url, js_path, scan_vulns, ai_enabled, bruteforce_enabled, analysis_type)
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
        return jsonify(result)

    except Exception as e:
        print(f"[!] Get status error: {e}")
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
                    'total_vulnerabilities': total_vulns
                },
                'vulnerabilities': {
                    'by_severity': vuln_by_severity,
                    'by_type': vuln_types,
                    'top_vulnerable_endpoints': top_vulnerable_endpoints
                },
                'endpoints': {
                    'by_method': method_counts,
                    'shadow_ratio': round((shadow_apis / total_endpoints * 100) if total_endpoints > 0 else 0, 1)
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
        return jsonify({'error': 'Failed to delete project', 'details': str(e)}), 500


@app.route('/api/vulnerability/<vuln_id>/generate-poc', methods=['POST'])
def generate_vulnerability_poc(vuln_id):
    """Generate PoC code for a specific vulnerability using AI."""
    try:
        # Get vulnerability from database
        with get_db() as db:
            from src.database.models import Vulnerability as VulnModel
            vuln_db = db.query(VulnModel).filter(VulnModel.id == vuln_id).first()
            
            if not vuln_db:
                return jsonify({'error': 'Vulnerability not found'}), 404
            
            # Check if PoC already exists
            if vuln_db.poc_code:
                return jsonify({
                    'vulnerability_id': vuln_id,
                    'poc_code': vuln_db.poc_code,
                    'message': 'PoC already exists'
                })
            
            # Convert to Vulnerability object
            from src.utils.models import Vulnerability, VulnerabilityLevel, HTTPMethod
            
            # vuln_db.level is already a VulnerabilitySeverity enum, use .value to get string
            level_str = vuln_db.level.value if hasattr(vuln_db.level, 'value') else str(vuln_db.level)
            
            vuln = Vulnerability(
                type=vuln_db.type,
                level=VulnerabilityLevel[level_str.upper()],
                endpoint=vuln_db.endpoint,
                method=HTTPMethod[vuln_db.method.upper()],
                description=vuln_db.description,
                evidence=vuln_db.evidence,
                recommendation=vuln_db.recommendation,
                cwe_id=vuln_db.cwe_id
            )
            
            # AI-based PoC generation only
            from src.analyzer.ai_analyzer import AIJSAnalyzer
            ai_analyzer = AIJSAnalyzer()
            
            if not ai_analyzer.enabled:
                return jsonify({
                    'error': 'AI PoC generation is not available',
                    'details': 'OpenAI API key is not configured. Please set OPENAI_API_KEY in config.yaml'
                }), 503
            
            print(f"[*] Generating AI-based PoC for vulnerability {vuln_id}")
            vulnerabilities = ai_analyzer.generate_vulnerability_poc([vuln])
            
            if not vulnerabilities or not vulnerabilities[0].poc_code:
                return jsonify({
                    'error': 'Failed to generate PoC',
                    'details': 'AI PoC generation failed. Please try again later.'
                }), 500
            
            poc_code = vulnerabilities[0].poc_code
            print(f"[+] AI PoC generated successfully")
            
            # Update database with PoC
            vuln_db.poc_code = poc_code
            db.commit()
            
            return jsonify({
                'vulnerability_id': vuln_id,
                'poc_code': poc_code,
                'message': 'PoC generated successfully'
            })
            
    except Exception as e:
        print(f"[!] Generate PoC error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate PoC', 'details': str(e)}), 500


@app.route('/api/scan/<scan_id>/generate-all-pocs', methods=['POST'])
def generate_all_pocs_for_scan(scan_id):
    """Generate PoC codes for all vulnerabilities in a scan."""
    try:
        with get_db() as db:
            from src.database.models import Vulnerability as VulnModel
            vulnerabilities = db.query(VulnModel).filter(VulnModel.scan_id == scan_id).all()
            
            if not vulnerabilities:
                return jsonify({'error': 'No vulnerabilities found for this scan'}), 404
            
            generated_count = 0
            skipped_count = 0
            error_count = 0
            
            # Initialize AI analyzer
            from src.analyzer.ai_analyzer import AIJSAnalyzer
            ai_analyzer = AIJSAnalyzer()
            
            if not ai_analyzer.enabled:
                return jsonify({
                    'error': 'AI PoC generation is not available',
                    'details': 'OpenAI API key is not configured. Please set OPENAI_API_KEY in config.yaml'
                }), 503
            
            from src.utils.models import Vulnerability, VulnerabilityLevel, HTTPMethod
            
            for vuln_db in vulnerabilities:
                try:
                    # Skip if PoC already exists
                    if vuln_db.poc_code:
                        skipped_count += 1
                        continue
                    
                    # Convert to Vulnerability object
                    # vuln_db.level is already a VulnerabilitySeverity enum, use .value to get string
                    level_str = vuln_db.level.value if hasattr(vuln_db.level, 'value') else str(vuln_db.level)
                    
                    vuln = Vulnerability(
                        type=vuln_db.type,
                        level=VulnerabilityLevel[level_str.upper()],
                        endpoint=vuln_db.endpoint,
                        method=HTTPMethod[vuln_db.method.upper()],
                        description=vuln_db.description,
                        evidence=vuln_db.evidence,
                        recommendation=vuln_db.recommendation,
                        cwe_id=vuln_db.cwe_id
                    )
                    
                    # Generate PoC using AI only
                    vulnerabilities_with_poc = ai_analyzer.generate_vulnerability_poc([vuln])
                    if vulnerabilities_with_poc and vulnerabilities_with_poc[0].poc_code:
                        poc_code = vulnerabilities_with_poc[0].poc_code
                        # Update database
                        vuln_db.poc_code = poc_code
                        generated_count += 1
                    else:
                        print(f"[!] Failed to generate PoC for vulnerability {vuln_db.id}")
                        error_count += 1
                    
                except Exception as e:
                    print(f"[!] Error generating PoC for vulnerability {vuln_db.id}: {e}")
                    error_count += 1
                    continue
            
            db.commit()
            
            return jsonify({
                'scan_id': scan_id,
                'generated': generated_count,
                'skipped': skipped_count,
                'errors': error_count,
                'message': f'PoC generation completed: {generated_count} generated, {skipped_count} skipped, {error_count} errors'
            })
            
    except Exception as e:
        print(f"[!] Generate all PoCs error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate PoCs', 'details': str(e)}), 500


@app.route('/api/endpoint/<int:endpoint_id>/curl', methods=['GET'])
def generate_curl_command(endpoint_id):
    """Generate curl commands for a specific endpoint."""
    try:
        with get_db() as db:
            from src.database.models import Endpoint
            endpoint_db = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
            
            if not endpoint_db:
                return jsonify({'error': 'Endpoint not found'}), 404
            
            # Convert to APIEndpoint model
            from src.utils.models import APIEndpoint, HTTPMethod
            from src.utils.curl_generator import CurlGenerator
            
            # Parse parameters from URL or body
            parameters = {}
            if endpoint_db.parameters:
                try:
                    parameters = json.loads(endpoint_db.parameters) if isinstance(endpoint_db.parameters, str) else endpoint_db.parameters
                except:
                    parameters = {}
            
            # Parse headers
            headers = {}
            if endpoint_db.headers:
                try:
                    headers = json.loads(endpoint_db.headers) if isinstance(endpoint_db.headers, str) else endpoint_db.headers
                except:
                    headers = {}
            
            api_endpoint = APIEndpoint(
                url=endpoint_db.url,
                method=HTTPMethod[endpoint_db.method.upper()],
                parameters=parameters,
                headers=headers,
                body_example=endpoint_db.body_example,
                source=endpoint_db.source
            )
            
            # Generate curl commands
            include_auth = request.args.get('include_auth', 'false').lower() == 'true'
            auth_token = request.args.get('auth_token', '')
            use_ai = request.args.get('use_ai', 'true').lower() == 'true'
            
            curl_commands = CurlGenerator.generate_curl(
                api_endpoint,
                include_auth=include_auth,
                auth_token=auth_token,
                use_ai=use_ai
            )
            
            return jsonify({
                'endpoint_id': endpoint_id,
                'url': endpoint_db.url,
                'method': endpoint_db.method,
                'curl_commands': curl_commands
            })
            
    except Exception as e:
        print(f"[!] Generate curl error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate curl command', 'details': str(e)}), 500


@app.route('/api/scan/<scan_id>/endpoints/curl-all', methods=['GET'])
def generate_all_curl_commands(scan_id):
    """Generate curl commands for all endpoints in a scan."""
    try:
        with get_db() as db:
            from src.database.models import Endpoint
            from src.utils.models import APIEndpoint, HTTPMethod
            from src.utils.curl_generator import CurlGenerator
            
            endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan_id).all()
            
            if not endpoints:
                return jsonify({'error': 'No endpoints found for this scan'}), 404
            
            include_auth = request.args.get('include_auth', 'false').lower() == 'true'
            auth_token = request.args.get('auth_token', '')
            
            all_curl_commands = []
            
            for endpoint_db in endpoints:
                # Parse parameters
                parameters = {}
                if endpoint_db.parameters:
                    try:
                        parameters = json.loads(endpoint_db.parameters) if isinstance(endpoint_db.parameters, str) else endpoint_db.parameters
                    except:
                        parameters = {}
                
                # Parse headers
                headers = {}
                if endpoint_db.headers:
                    try:
                        headers = json.loads(endpoint_db.headers) if isinstance(endpoint_db.headers, str) else endpoint_db.headers
                    except:
                        headers = {}
                
                api_endpoint = APIEndpoint(
                    url=endpoint_db.url,
                    method=HTTPMethod[endpoint_db.method.upper()],
                    parameters=parameters,
                    headers=headers,
                    body_example=endpoint_db.body_example,
                    source=endpoint_db.source
                )
                
                use_ai = request.args.get('use_ai', 'true').lower() == 'true'
                
                curl_commands = CurlGenerator.generate_curl(
                    api_endpoint,
                    include_auth=include_auth,
                    auth_token=auth_token,
                    use_ai=use_ai
                )
                
                all_curl_commands.append({
                    'endpoint_id': endpoint_db.id,
                    'url': endpoint_db.url,
                    'method': endpoint_db.method,
                    'curl_commands': curl_commands
                })
            
            return jsonify({
                'scan_id': scan_id,
                'total_endpoints': len(all_curl_commands),
                'endpoints': all_curl_commands
            })
            
    except Exception as e:
        print(f"[!] Generate all curl error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate curl commands', 'details': str(e)}), 500


@app.route('/api/scan/<scan_id>/postman-collection', methods=['GET'])
def generate_postman_collection(scan_id):
    """Generate Postman collection for all endpoints in a scan."""
    try:
        with get_db() as db:
            from src.database.models import Endpoint, Scan
            from src.utils.models import APIEndpoint, HTTPMethod
            from src.utils.curl_generator import CurlGenerator
            
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                return jsonify({'error': 'Scan not found'}), 404
            
            endpoints_db = db.query(Endpoint).filter(Endpoint.scan_id == scan_id).all()
            
            if not endpoints_db:
                return jsonify({'error': 'No endpoints found for this scan'}), 404
            
            # Convert to APIEndpoint objects
            api_endpoints = []
            for endpoint_db in endpoints_db:
                parameters = {}
                if endpoint_db.parameters:
                    try:
                        parameters = json.loads(endpoint_db.parameters) if isinstance(endpoint_db.parameters, str) else endpoint_db.parameters
                    except:
                        parameters = {}
                
                headers = {}
                if endpoint_db.headers:
                    try:
                        headers = json.loads(endpoint_db.headers) if isinstance(endpoint_db.headers, str) else endpoint_db.headers
                    except:
                        headers = {}
                
                api_endpoint = APIEndpoint(
                    url=endpoint_db.url,
                    method=HTTPMethod[endpoint_db.method.upper()],
                    parameters=parameters,
                    headers=headers,
                    body_example=endpoint_db.body_example,
                    source=endpoint_db.source
                )
                api_endpoints.append(api_endpoint)
            
            # Generate Postman collection
            collection_name = f"Scan {scan_id} - {scan.target_url}"
            collection = CurlGenerator.generate_postman_collection(
                api_endpoints,
                collection_name
            )
            
            return jsonify(collection)
            
    except Exception as e:
        print(f"[!] Generate Postman collection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate Postman collection', 'details': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'API server is running'})


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
