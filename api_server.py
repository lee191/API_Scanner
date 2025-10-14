"""Flask API server for Shadow API Scanner with DB integration."""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import subprocess
import threading
from uuid import uuid4

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

        # Add discovered_paths from JSON file if scan is completed
        if result.get('status') == 'completed':
            try:
                output_dir = Path(__file__).parent / 'output' / 'web-scans' / scan_id
                json_files = list(output_dir.glob('*.json'))
                if json_files:
                    with open(json_files[0], 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        discovered_paths = json_data.get('discovered_paths', [])
                        if discovered_paths and result.get('result'):
                            result['result']['discovered_paths'] = discovered_paths
                            # Update statistics if needed
                            if 'statistics' in result['result']:
                                result['result']['statistics']['discovered_paths'] = len(discovered_paths)
            except Exception as e:
                print(f"[!] Failed to load discovered_paths: {e}")

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
