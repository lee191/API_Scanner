"""Database repository for CRUD operations."""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import uuid4

from src.database.models import Project, Scan, Endpoint, Vulnerability, DiscoveredPath, ScanStatus, VulnerabilitySeverity
from src.utils.curl_generator import CurlGenerator
from src.utils.api_classifier import APIClassifier

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """Get current time in KST."""
    return datetime.now(KST)
from src.utils.models import ScanResult, APIEndpoint, Vulnerability as VulnModel


class ProjectRepository:
    """Repository for Project operations."""

    @staticmethod
    def create_project(
        db: Session,
        name: str,
        description: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project = Project(
            project_id=str(uuid4()),
            name=name,
            description=description
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project_by_id(db: Session, project_id: str) -> Optional[Project]:
        """Get project by project_id."""
        return db.query(Project).filter(Project.project_id == project_id).first()

    @staticmethod
    def get_all_projects(db: Session, limit: int = 100, offset: int = 0) -> List[Project]:
        """Get all projects with pagination."""
        return db.query(Project).order_by(desc(Project.created_at)).limit(limit).offset(offset).all()

    @staticmethod
    def update_project(
        db: Session,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Project]:
        """Update project information."""
        project = ProjectRepository.get_project_by_id(db, project_id)
        if project:
            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            project.updated_at = get_kst_now()
            db.commit()
            db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        """Delete a project and all related scans."""
        project = ProjectRepository.get_project_by_id(db, project_id)
        if project:
            db.delete(project)
            db.commit()
            return True
        return False

    @staticmethod
    def get_project_with_scans(db: Session, project_id: str) -> Optional[dict]:
        """Get project with all its scans."""
        project = ProjectRepository.get_project_by_id(db, project_id)
        if not project:
            return None

        scans = [
            {
                'scan_id': scan.scan_id,
                'target_url': scan.target_url,
                'status': scan.status.value,
                'created_at': scan.created_at.isoformat() if scan.created_at else None,
                'statistics': {
                    'total_endpoints': scan.total_endpoints,
                    'shadow_apis': scan.shadow_apis,
                    'public_apis': scan.public_apis,
                    'total_vulnerabilities': scan.total_vulnerabilities,
                    'discovered_paths': len(scan.discovered_paths) if scan.discovered_paths else 0
                }
            }
            for scan in project.scans
        ]

        return {
            'project_id': project.project_id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None,
            'scan_count': len(scans),
            'scans': scans
        }


class ScanRepository:
    """Repository for Scan operations."""

    @staticmethod
    def create_scan(
        db: Session,
        scan_id: str,
        target_url: str,
        js_path: Optional[str] = None,
        project_id: Optional[str] = None,
        ai_enabled: bool = True,
        bruteforce_enabled: bool = False,
        analysis_type: str = 'full_scan'
    ) -> Scan:
        """Create a new scan record."""
        # Resolve project_id to internal ID if provided
        db_project_id = None
        if project_id:
            project = ProjectRepository.get_project_by_id(db, project_id)
            if project:
                db_project_id = project.id

        scan = Scan(
            scan_id=scan_id,
            project_id=db_project_id,
            target_url=target_url,
            js_path=js_path,
            status=ScanStatus.PENDING,
            ai_enabled=ai_enabled,
            bruteforce_enabled=bruteforce_enabled,
            analysis_type=analysis_type,
            progress=0,
            message='Scan queued'
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan

    @staticmethod
    def get_scan_by_id(db: Session, scan_id: str) -> Optional[Scan]:
        """Get scan by scan_id."""
        return db.query(Scan).filter(Scan.scan_id == scan_id).first()

    @staticmethod
    def update_scan_status(
        db: Session,
        scan_id: str,
        status: ScanStatus,
        progress: int,
        message: str
    ) -> Optional[Scan]:
        """Update scan status."""
        scan = ScanRepository.get_scan_by_id(db, scan_id)
        if scan:
            scan.status = status
            scan.progress = progress
            scan.message = message

            if status == ScanStatus.RUNNING and not scan.started_at:
                scan.started_at = get_kst_now()
            elif status == ScanStatus.COMPLETED or status == ScanStatus.FAILED:
                scan.completed_at = get_kst_now()

            db.commit()
            db.refresh(scan)
        return scan

    @staticmethod
    def save_scan_result(
        db: Session,
        scan_id: str,
        scan_result: ScanResult,
        output_path: Optional[str] = None
    ) -> Optional[Scan]:
        """Save complete scan result to database."""
        scan = ScanRepository.get_scan_by_id(db, scan_id)
        if not scan:
            return None

        # Update scan statistics
        scan.total_endpoints = scan_result.statistics.get('total_endpoints', 0)
        scan.shadow_apis = scan_result.statistics.get('shadow_apis', 0)
        scan.public_apis = scan_result.statistics.get('public_apis', 0)
        scan.total_vulnerabilities = scan_result.statistics.get('total_vulnerabilities', 0)
        scan.output_path = output_path
        scan.status = ScanStatus.COMPLETED
        scan.progress = 100
        scan.message = 'Scan completed successfully'
        scan.completed_at = get_kst_now()

        # Save endpoints
        for ep in scan_result.endpoints:
            # Classify endpoint using intelligent classifier
            is_shadow = APIClassifier.classify(ep, source=ep.source)

            # Generate curl command for validation
            try:
                curl_command = CurlGenerator.generate(ep)
            except Exception as e:
                print(f"[!] Failed to generate curl for {ep.url}: {e}")
                curl_command = None

            endpoint = Endpoint(
                scan_id=scan.id,
                url=ep.url,
                method=ep.method.value if hasattr(ep.method, 'value') else str(ep.method),
                is_shadow_api=is_shadow,
                parameters=ep.parameters,
                headers=ep.headers,
                body_example=ep.body_example,
                response_example=ep.response_example,
                poc_code=ep.poc_code,
                curl_command=curl_command,
                status_code=ep.status_code,
                source=ep.source
            )
            db.add(endpoint)

        # Save vulnerabilities
        for vuln in scan_result.vulnerabilities:
            vulnerability = Vulnerability(
                scan_id=scan.id,
                type=vuln.type,
                level=VulnerabilitySeverity[vuln.level.upper()] if hasattr(vuln, 'level') else VulnerabilitySeverity.INFO,
                endpoint=vuln.endpoint,
                method=vuln.method.value if hasattr(vuln.method, 'value') else str(vuln.method),
                description=vuln.description,
                evidence=vuln.evidence,
                recommendation=vuln.recommendation,
                poc_code=getattr(vuln, 'poc_code', None),
                cwe_id=vuln.cwe_id
            )
            db.add(vulnerability)

        # Save discovered paths (from bruteforce)
        if hasattr(scan_result, 'discovered_paths') and scan_result.discovered_paths:
            for path_data in scan_result.discovered_paths:
                discovered_path = DiscoveredPath(
                    scan_id=scan.id,
                    path=path_data.get('path', ''),
                    status_code=path_data.get('status_code', 0),
                    content_length=path_data.get('content_length'),
                    content_type=path_data.get('content_type')
                )
                db.add(discovered_path)

        db.commit()
        db.refresh(scan)
        return scan

    @staticmethod
    def get_scan_with_details(db: Session, scan_id: str) -> Optional[dict]:
        """Get scan with all endpoints and vulnerabilities."""
        scan = ScanRepository.get_scan_by_id(db, scan_id)
        if not scan:
            return None

        # Add endpoints
        shadow_apis = []
        public_apis = []
        for ep in scan.endpoints:
            ep_dict = ep.to_dict()
            if ep.is_shadow_api:
                shadow_apis.append(ep_dict)
            else:
                public_apis.append(ep_dict)

        # Add vulnerabilities
        vulnerabilities = [v.to_dict() for v in scan.vulnerabilities]

        # Add discovered paths
        discovered_paths = [dp.to_dict() for dp in scan.discovered_paths]

        # Calculate status code counts
        all_endpoints = scan.endpoints
        count_2xx = len([e for e in all_endpoints if e.status_code and 200 <= e.status_code < 300])
        count_3xx = len([e for e in all_endpoints if e.status_code and 300 <= e.status_code < 400])
        count_4xx = len([e for e in all_endpoints if e.status_code and 400 <= e.status_code < 500])
        count_5xx = len([e for e in all_endpoints if e.status_code and 500 <= e.status_code < 600])
        
        # Build result dictionary with nested structure for frontend
        result = {
            'scan_id': scan.scan_id,
            'target_url': scan.target_url,
            'status': scan.status.value,
            'progress': scan.progress,
            'message': scan.message,
            'created_at': scan.created_at.isoformat() if scan.created_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'result': {
                'statistics': {
                    'total_endpoints': scan.total_endpoints,
                    'shadow_apis': scan.shadow_apis,
                    'public_apis': scan.public_apis,
                    'total_vulnerabilities': scan.total_vulnerabilities,
                    'discovered_paths': len(discovered_paths),
                    'count_2xx': count_2xx,
                    'count_3xx': count_3xx,
                    'count_4xx': count_4xx,
                    'count_5xx': count_5xx
                },
                'shadow_apis': shadow_apis,
                'public_apis': public_apis,
                'endpoints': shadow_apis + public_apis,
                'vulnerabilities': vulnerabilities,
                'discovered_paths': discovered_paths
            }
        }

        return result

    @staticmethod
    def get_all_scans(db: Session, limit: int = 10, offset: int = 0) -> List[Scan]:
        """Get all scans with pagination."""
        return db.query(Scan).order_by(desc(Scan.created_at)).limit(limit).offset(offset).all()

    @staticmethod
    def get_scan_history(db: Session, limit: int = 10) -> List[dict]:
        """Get scan history for display."""
        scans = ScanRepository.get_all_scans(db, limit=limit)
        result = []
        
        for scan in scans:
            # Calculate status code counts from endpoints
            count_2xx = len([e for e in scan.endpoints if e.status_code and 200 <= e.status_code < 300])
            count_3xx = len([e for e in scan.endpoints if e.status_code and 300 <= e.status_code < 400])
            count_4xx = len([e for e in scan.endpoints if e.status_code and 400 <= e.status_code < 500])
            count_5xx = len([e for e in scan.endpoints if e.status_code and 500 <= e.status_code < 600])
            
            result.append({
                'id': scan.scan_id,
                'target': scan.target_url,
                'timestamp': scan.created_at.isoformat() if scan.created_at else None,
                'status': scan.status.value,
                'result': {
                    'statistics': {
                        'total_endpoints': scan.total_endpoints,
                        'shadow_apis': scan.shadow_apis,
                        'public_apis': scan.public_apis,
                        'total_vulnerabilities': scan.total_vulnerabilities,
                        'discovered_paths': len(scan.discovered_paths) if scan.discovered_paths else 0,
                        'count_2xx': count_2xx,
                        'count_3xx': count_3xx,
                        'count_4xx': count_4xx,
                        'count_5xx': count_5xx
                    }
                }
            })
        
        return result

    @staticmethod
    def delete_scan(db: Session, scan_id: str) -> bool:
        """Delete a scan and all related data."""
        scan = ScanRepository.get_scan_by_id(db, scan_id)
        if scan:
            db.delete(scan)
            db.commit()
            return True
        return False
