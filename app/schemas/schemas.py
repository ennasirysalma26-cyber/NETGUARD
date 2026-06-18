from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import re


# ════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "Bearer"
    expires_in:    int


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in:   int


class UserOut(BaseModel):
    id:         str
    username:   str
    email:      str
    role:       str
    created_at: datetime

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
#  DEVICES
# ════════════════════════════════════════════════════════════

DeviceType   = Literal["Routeur", "Switch", "Ordinateur", "AP", "Imprimante"]
DeviceStatus = Literal["Actif", "Panne", "Maintenance"]


def _validate_ip(v: str) -> str:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, v):
        raise ValueError("Format IPv4 invalide")
    parts = v.split(".")
    if any(int(p) > 255 for p in parts):
        raise ValueError("Octet hors plage (0-255)")
    return v


def _validate_mac(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
    if not re.match(pattern, v):
        raise ValueError("Format MAC invalide (XX:XX:XX:XX:XX:XX)")
    return v.upper()


class DeviceCreate(BaseModel):
    name:           str            = Field(..., max_length=100)
    type:           DeviceType
    model:          Optional[str]  = Field(None, max_length=150)
    ip_address:     str
    mac_address:    Optional[str]  = None
    location:       Optional[str]  = Field(None, max_length=200)
    status:         DeviceStatus   = "Actif"
    snmp_enabled:   bool           = False
    snmp_community: Optional[str]  = None
    snmp_version:   Optional[str]  = "2c"
    notes:          Optional[str]  = Field(None, max_length=500)

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v): return _validate_ip(v)

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v): return _validate_mac(v)


class DeviceUpdate(BaseModel):
    name:           Optional[str]         = Field(None, max_length=100)
    type:           Optional[DeviceType]  = None
    model:          Optional[str]         = None
    ip_address:     Optional[str]         = None
    mac_address:    Optional[str]         = None
    location:       Optional[str]         = None
    status:         Optional[DeviceStatus]= None
    snmp_enabled:   Optional[bool]        = None
    snmp_community: Optional[str]         = None
    notes:          Optional[str]         = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v):
        return _validate_ip(v) if v else v

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v): return _validate_mac(v)


class DeviceOut(BaseModel):
    id:             str
    name:           str
    type:           str
    model:          Optional[str]
    ip_address:     str
    mac_address:    Optional[str]
    location:       Optional[str]
    status:         str
    snmp_enabled:   bool
    snmp_community: Optional[str]
    notes:          Optional[str]
    last_seen:      Optional[datetime]
    created_at:     datetime
    updated_at:     datetime

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    data:       List[DeviceOut]
    pagination: dict


# ════════════════════════════════════════════════════════════
#  PROBE
# ════════════════════════════════════════════════════════════

class PingRequest(BaseModel):
    count:   int = Field(4,    ge=1, le=20)
    timeout: int = Field(1000, ge=100, le=10000)


class PingResult(BaseModel):
    device_id:    str
    ip:           str
    status:       str
    rtt_avg_ms:   Optional[float]
    rtt_min_ms:   Optional[float]
    rtt_max_ms:   Optional[float]
    packet_loss:  float
    probed_at:    datetime


class ProbePoint(BaseModel):
    ts:       datetime
    rtt_avg:  Optional[float]
    loss:     float


class ProbeHistoryResponse(BaseModel):
    device_id:  str
    resolution: str
    points:     List[ProbePoint]


class SnmpResult(BaseModel):
    device_id:  str
    probed_at:  datetime
    system:     dict
    resources:  dict
    interfaces: List[dict]


class ScanStatusResponse(BaseModel):
    scanned_at: datetime
    summary:    dict
    devices:    List[dict]


# ════════════════════════════════════════════════════════════
#  INTERVENTIONS
# ════════════════════════════════════════════════════════════

InterventionType = Literal["Panne", "Maintenance", "Configuration", "MAJ"]


class InterventionCreate(BaseModel):
    device_id:   str
    type:        InterventionType
    description: str = Field(..., min_length=5, max_length=1000)


class InterventionOut(BaseModel):
    id:          str
    device_id:   str
    device_name: Optional[str] = None
    type:        str
    description: str
    author:      Optional[str] = None
    created_at:  datetime

    model_config = {"from_attributes": True}


class InterventionListResponse(BaseModel):
    data:       List[InterventionOut]
    pagination: dict


# ════════════════════════════════════════════════════════════
#  ALERTS
# ════════════════════════════════════════════════════════════

class AlertOut(BaseModel):
    id:              str
    device_id:       str
    device_name:     Optional[str] = None
    severity:        str
    message:         str
    acknowledged:    bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    triggered_at:    datetime

    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    note: Optional[str] = None


# ════════════════════════════════════════════════════════════
#  TOPOLOGY
# ════════════════════════════════════════════════════════════

class TopologyNode(BaseModel):
    id:     str
    name:   str
    type:   str
    status: str
    ip:     str
    x:      float
    y:      float


class TopologyEdge(BaseModel):
    id:     str
    source: str
    target: str
    label:  Optional[str]
    type:   str


class TopologyResponse(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]


class NodePositionUpdate(BaseModel):
    x: float
    y: float


class LinkCreate(BaseModel):
    source_id: str
    target_id: str
    label:     Optional[str]  = None
    type:      Optional[str]  = "ethernet"


class Pagination(BaseModel):
    page:  int
    limit: int
    total: int
    pages: int
