"""Database repository for CRUD operations."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import uuid4

from src.database.models import Project, Scan, Endpoint, Vulnerability, ScanStatus, VulnerabilitySeverity
from src.utils.models import ScanResult, APIEndpoint, Vulnerability as VulnModel
from src.scanner.vulnerability_scanner import VulnerabilityScanner


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
            project.updated_at = datetime.utcnow()
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
                    'total_vulnerabilities': scan.total_vulnerabilities
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
        scan_vulns: bool = True,
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
            scan_vulns=scan_vulns,
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
                scan.started_at = datetime.utcnow()
            elif status == ScanStatus.COMPLETED or status == ScanStatus.FAILED:
                scan.completed_at = datetime.utcnow()

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
        scan.completed_at = datetime.utcnow()

        # Save endpoints
        for ep in scan_result.endpoints:
            endpoint = Endpoint(
                scan_id=scan.id,
                url=ep.url,
                method=ep.method.value if hasattr(ep.method, 'value') else str(ep.method),
                is_shadow_api=VulnerabilityScanner.is_shadow_api(ep),
                parameters=ep.parameters,
                headers=ep.headers,
                body_example=ep.body_example,
                response_example=ep.response_example,
                poc_code=ep.poc_code,
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
                    'total_vulnerabilities': scan.total_vulnerabilities
                },
                'shadow_apis': shadow_apis,
                'public_apis': public_apis,
                'endpoints': shadow_apis + public_apis,
                'vulnerabilities': vulnerabilities
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
        return [
            {
                'id': scan.scan_id,
                'target': scan.target_url,
                'timestamp': scan.created_at.isoformat() if scan.created_at else None,
                'status': scan.status.value,
                'result': {
                    'statistics': {
                        'total_endpoints': scan.total_endpoints,
                        'shadow_apis': scan.shadow_apis,
                        'public_apis': scan.public_apis,
                        'total_vulnerabilities': scan.total_vulnerabilities
                    }
                }
            }
            for scan in scans
        ]

    @staticmethod
    def delete_scan(db: Session, scan_id: str) -> bool:
        """Delete a scan and all related data."""
        scan = ScanRepository.get_scan_by_id(db, scan_id)
        if scan:
            db.delete(scan)
            db.commit()
            return True
        return False
