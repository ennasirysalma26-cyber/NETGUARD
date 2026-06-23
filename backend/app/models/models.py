import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float,
    Integer, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

# ─── Helpers ────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)

def new_uuid():
    return str(uuid.uuid4())


# ─── User ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, default=new_uuid)
    username      = Column(String(50),  unique=True, nullable=False, index=True)
    email         = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role          = Column(SAEnum("admin", "technicien", "lecteur", name="user_role"),
                           nullable=False, default="lecteur")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), default=now_utc)

    interventions = relationship("Intervention", back_populates="author_user",
                                 foreign_keys="Intervention.author_id")


# ─── Device ─────────────────────────────────────────────────────────────────

class Device(Base):
    __tablename__ = "devices"

    id             = Column(String, primary_key=True, default=new_uuid)
    name           = Column(String(100), unique=True, nullable=False, index=True)
    type           = Column(SAEnum("Routeur","Switch","Ordinateur","AP","Imprimante",
                                   name="device_type"), nullable=False)
    model          = Column(String(150))
    ip_address     = Column(String(45),  unique=True, nullable=False, index=True)
    mac_address    = Column(String(17))
    location       = Column(String(200))
    status         = Column(SAEnum("Actif","Panne","Maintenance", name="device_status"),
                            nullable=False, default="Actif")
    snmp_enabled   = Column(Boolean, default=False)
    snmp_community = Column(String(100))
    snmp_version   = Column(String(10), default="2c")
    notes          = Column(Text)
    last_seen      = Column(DateTime(timezone=True))
    pos_x          = Column(Float, default=0.0)
    pos_y          = Column(Float, default=0.0)
    created_at     = Column(DateTime(timezone=True), default=now_utc)
    updated_at     = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    interventions  = relationship("Intervention", back_populates="device",
                                  cascade="all, delete-orphan")
    probe_results  = relationship("ProbeResult",  back_populates="device",
                                  cascade="all, delete-orphan")
    alerts         = relationship("Alert",        back_populates="device",
                                  cascade="all, delete-orphan")
    links_source   = relationship("TopologyLink", foreign_keys="TopologyLink.source_id",
                                  back_populates="source", cascade="all, delete-orphan")
    links_target   = relationship("TopologyLink", foreign_keys="TopologyLink.target_id",
                                  back_populates="target", cascade="all, delete-orphan")


# ─── Probe Result ────────────────────────────────────────────────────────────

class ProbeResult(Base):
    __tablename__ = "probe_results"

    id          = Column(String, primary_key=True, default=new_uuid)
    device_id   = Column(String, ForeignKey("devices.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    rtt_avg_ms  = Column(Float)
    rtt_min_ms  = Column(Float)
    rtt_max_ms  = Column(Float)
    packet_loss = Column(Float, default=0.0)
    status      = Column(String(20), default="up")
    recorded_at = Column(DateTime(timezone=True), default=now_utc, index=True)

    device = relationship("Device", back_populates="probe_results")


# ─── Intervention ────────────────────────────────────────────────────────────

class Intervention(Base):
    __tablename__ = "interventions"

    id          = Column(String, primary_key=True, default=new_uuid)
    device_id   = Column(String, ForeignKey("devices.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    author_id   = Column(String, ForeignKey("users.id"), nullable=False)
    type        = Column(SAEnum("Panne","Maintenance","Configuration","MAJ",
                                name="intervention_type"), nullable=False)
    description = Column(Text, nullable=False)
    created_at  = Column(DateTime(timezone=True), default=now_utc, index=True)

    device      = relationship("Device",       back_populates="interventions")
    author_user = relationship("User",         back_populates="interventions",
                               foreign_keys=[author_id])


# ─── Alert ──────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id               = Column(String, primary_key=True, default=new_uuid)
    device_id        = Column(String, ForeignKey("devices.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    severity         = Column(SAEnum("critical","warning","info", name="alert_severity"),
                              nullable=False)
    message          = Column(Text, nullable=False)
    acknowledged     = Column(Boolean, default=False)
    acknowledged_by  = Column(String)
    acknowledged_at  = Column(DateTime(timezone=True))
    triggered_at     = Column(DateTime(timezone=True), default=now_utc)

    device = relationship("Device", back_populates="alerts")


# ─── Topology Link ───────────────────────────────────────────────────────────

class TopologyLink(Base):
    __tablename__ = "topology_links"

    id         = Column(String, primary_key=True, default=new_uuid)
    source_id  = Column(String, ForeignKey("devices.id", ondelete="CASCADE"),
                        nullable=False)
    target_id  = Column(String, ForeignKey("devices.id", ondelete="CASCADE"),
                        nullable=False)
    label      = Column(String(100))
    link_type  = Column(SAEnum("ethernet","fiber","wireless","vpn",
                               name="link_type"), default="ethernet")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    source = relationship("Device", foreign_keys=[source_id], back_populates="links_source")
    target = relationship("Device", foreign_keys=[target_id], back_populates="links_target")
