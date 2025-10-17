"""Database models for Shadow API Scanner."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """Get current time in KST."""
    return datetime.now(KST)


class ScanStatus(enum.Enum):
    """Scan status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class VulnerabilitySeverity(enum.Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Project(Base):
    """Project model."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    project_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=get_kst_now, nullable=False)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # Relationships
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'scan_count': len(self.scans) if self.scans else 0
        }


class Scan(Base):
    """Scan model."""
    __tablename__ = 'scans'

    id = Column(Integer, primary_key=True)
    scan_id = Column(String(36), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    target_url = Column(String(500), nullable=False)
    js_path = Column(String(500), nullable=True)

    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)

    ai_enabled = Column(Boolean, default=True)
    bruteforce_enabled = Column(Boolean, default=False)
    analysis_type = Column(String(50), default='full_scan')

    # Statistics
    total_endpoints = Column(Integer, default=0)
    shadow_apis = Column(Integer, default=0)
    public_apis = Column(Integer, default=0)
    total_vulnerabilities = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=get_kst_now, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Output path
    output_path = Column(String(500), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scans")
    endpoints = relationship("Endpoint", back_populates="scan", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    discovered_paths = relationship("DiscoveredPath", back_populates="scan", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'project_id': self.project_id,
            'target_url': self.target_url,
            'js_path': self.js_path,
            'status': self.status.value,
            'progress': self.progress,
            'message': self.message,
            'ai_enabled': self.ai_enabled,
            'bruteforce_enabled': self.bruteforce_enabled,
            'analysis_type': self.analysis_type,
            'statistics': {
                'total_endpoints': self.total_endpoints,
                'shadow_apis': self.shadow_apis,
                'public_apis': self.public_apis,
                'total_vulnerabilities': self.total_vulnerabilities
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_path': self.output_path
        }


class Endpoint(Base):
    """API Endpoint model."""
    __tablename__ = 'endpoints'

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False, index=True)

    url = Column(String(1000), nullable=False)
    method = Column(String(10), nullable=False)

    is_shadow_api = Column(Boolean, default=False)

    parameters = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    body_example = Column(Text, nullable=True)
    response_example = Column(Text, nullable=True)

    poc_code = Column(Text, nullable=True)
    curl_command = Column(Text, nullable=True)

    status_code = Column(Integer, nullable=True)
    source = Column(String(200), nullable=True)

    timestamp = Column(DateTime, default=get_kst_now)

    # Relationship
    scan = relationship("Scan", back_populates="endpoints")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'method': self.method,
            'is_shadow_api': self.is_shadow_api,
            'parameters': self.parameters,
            'headers': self.headers,
            'body_example': self.body_example,
            'response_example': self.response_example,
            'poc_code': self.poc_code,
            'curl_command': self.curl_command,
            'status_code': self.status_code,
            'source': self.source,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Vulnerability(Base):
    """Vulnerability model."""
    __tablename__ = 'vulnerabilities'

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False, index=True)

    type = Column(String(100), nullable=False)
    level = Column(SQLEnum(VulnerabilitySeverity), nullable=False)

    endpoint = Column(String(1000), nullable=False)
    method = Column(String(10), nullable=False)

    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=False)

    poc_code = Column(Text, nullable=True)

    cwe_id = Column(String(20), nullable=True)

    timestamp = Column(DateTime, default=get_kst_now)

    # Relationship
    scan = relationship("Scan", back_populates="vulnerabilities")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'level': self.level.value,
            'endpoint': self.endpoint,
            'method': self.method,
            'description': self.description,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'poc_code': self.poc_code,
            'cwe_id': self.cwe_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class DiscoveredPath(Base):
    """Discovered Path model (from directory bruteforce)."""
    __tablename__ = 'discovered_paths'

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False, index=True)

    path = Column(String(1000), nullable=False)
    status_code = Column(Integer, nullable=False)
    content_length = Column(Integer, nullable=True)
    content_type = Column(String(200), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    scan = relationship("Scan", back_populates="discovered_paths")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'path': self.path,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'content_type': self.content_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
