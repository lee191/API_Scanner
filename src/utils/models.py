"""Data models for Shadow API Scanner."""

from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timezone, timedelta
from enum import Enum

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """Get current time in KST."""
    return datetime.now(KST)


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class VulnerabilityLevel(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class APIEndpoint(BaseModel):
    """API endpoint information."""
    url: str
    method: HTTPMethod
    parameters: Dict[str, str] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    body_example: Optional[str] = None
    response_example: Optional[str] = None
    poc_code: Optional[str] = None  # Proof of Concept code to test the endpoint
    status_code: Optional[int] = None
    source: str = "unknown"  # 'proxy', 'js_analysis'
    timestamp: datetime = Field(default_factory=get_kst_now)

    class Config:
        use_enum_values = True


class Vulnerability(BaseModel):
    """Security vulnerability information."""
    type: str
    level: VulnerabilityLevel
    endpoint: str
    method: HTTPMethod
    description: str
    evidence: str
    recommendation: str
    poc_code: Optional[str] = None  # Proof of Concept code to exploit the vulnerability
    cwe_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=get_kst_now)

    class Config:
        use_enum_values = True


class ScanResult(BaseModel):
    """Complete scan result."""
    target: str
    scan_start: datetime
    scan_end: Optional[datetime] = None
    endpoints: List[APIEndpoint] = Field(default_factory=list)
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    discovered_paths: List[Dict[str, Any]] = Field(default_factory=list)  # 브루트포싱으로 발견된 경로 (상세 정보 포함)
    statistics: Dict[str, int] = Field(default_factory=dict)

    def add_endpoint(self, endpoint: APIEndpoint):
        """Add endpoint to results."""
        self.endpoints.append(endpoint)

    def add_vulnerability(self, vuln: Vulnerability):
        """Add vulnerability to results."""
        self.vulnerabilities.append(vuln)

    def finalize(self):
        """Finalize scan and calculate statistics."""
        self.scan_end = get_kst_now()
        self.statistics = {
            "total_endpoints": len(self.endpoints),
            "total_vulnerabilities": len(self.vulnerabilities),
            "discovered_paths": len(self.discovered_paths),
            "critical": len([v for v in self.vulnerabilities if v.level == VulnerabilityLevel.CRITICAL]),
            "high": len([v for v in self.vulnerabilities if v.level == VulnerabilityLevel.HIGH]),
            "medium": len([v for v in self.vulnerabilities if v.level == VulnerabilityLevel.MEDIUM]),
            "low": len([v for v in self.vulnerabilities if v.level == VulnerabilityLevel.LOW]),
        }
