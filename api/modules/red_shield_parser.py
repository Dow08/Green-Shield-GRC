from pydantic import BaseModel, Field
from typing import List, Optional

class RedShieldService(BaseModel):
    port: int
    protocol: str
    name: str
    tls_weak: Optional[bool] = False

class RedShieldAsset(BaseModel):
    ip: str
    os: Optional[str] = "Inconnu"
    services: List[RedShieldService] = []

class RedShieldVulnerability(BaseModel):
    cve: str
    severity: str
    target_ip: str
    description: Optional[str] = ""

class RedShieldSecurityControls(BaseModel):
    defender_active: Optional[bool] = False
    hids_alerts: Optional[int] = 0

class RedShieldExport(BaseModel):
    export_version: str
    timestamp: str
    assets: List[RedShieldAsset] = []
    vulnerabilities: List[RedShieldVulnerability] = []
    security_controls: Optional[RedShieldSecurityControls] = None
