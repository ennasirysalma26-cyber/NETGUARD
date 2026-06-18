"""Initial schema — all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id",            sa.String,  primary_key=True),
        sa.Column("username",      sa.String(50),  nullable=False, unique=True),
        sa.Column("email",         sa.String(120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("role",          sa.String(20),  nullable=False, default="lecteur"),
        sa.Column("is_active",     sa.Boolean,     default=True),
        sa.Column("created_at",    sa.DateTime(timezone=True)),
    )

    op.create_table(
        "devices",
        sa.Column("id",             sa.String,  primary_key=True),
        sa.Column("name",           sa.String(100), nullable=False, unique=True),
        sa.Column("type",           sa.String(50),  nullable=False),
        sa.Column("model",          sa.String(150)),
        sa.Column("ip_address",     sa.String(45),  nullable=False, unique=True),
        sa.Column("mac_address",    sa.String(17)),
        sa.Column("location",       sa.String(200)),
        sa.Column("status",         sa.String(20),  nullable=False, default="Actif"),
        sa.Column("snmp_enabled",   sa.Boolean,     default=False),
        sa.Column("snmp_community", sa.String(100)),
        sa.Column("snmp_version",   sa.String(10),  default="2c"),
        sa.Column("notes",          sa.Text),
        sa.Column("last_seen",      sa.DateTime(timezone=True)),
        sa.Column("pos_x",          sa.Float,       default=0.0),
        sa.Column("pos_y",          sa.Float,       default=0.0),
        sa.Column("created_at",     sa.DateTime(timezone=True)),
        sa.Column("updated_at",     sa.DateTime(timezone=True)),
    )
    op.create_index("ix_devices_ip",   "devices", ["ip_address"])
    op.create_index("ix_devices_name", "devices", ["name"])

    op.create_table(
        "probe_results",
        sa.Column("id",          sa.String, primary_key=True),
        sa.Column("device_id",   sa.String, sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rtt_avg_ms",  sa.Float),
        sa.Column("rtt_min_ms",  sa.Float),
        sa.Column("rtt_max_ms",  sa.Float),
        sa.Column("packet_loss", sa.Float, default=0.0),
        sa.Column("status",      sa.String(20)),
        sa.Column("recorded_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_probe_device",  "probe_results", ["device_id"])
    op.create_index("ix_probe_recorded","probe_results", ["recorded_at"])

    op.create_table(
        "interventions",
        sa.Column("id",          sa.String, primary_key=True),
        sa.Column("device_id",   sa.String, sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id",   sa.String, sa.ForeignKey("users.id"),  nullable=False),
        sa.Column("type",        sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at",  sa.DateTime(timezone=True)),
    )

    op.create_table(
        "alerts",
        sa.Column("id",              sa.String, primary_key=True),
        sa.Column("device_id",       sa.String, sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("severity",        sa.String(20), nullable=False),
        sa.Column("message",         sa.Text, nullable=False),
        sa.Column("acknowledged",    sa.Boolean, default=False),
        sa.Column("acknowledged_by", sa.String),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("triggered_at",    sa.DateTime(timezone=True)),
    )

    op.create_table(
        "topology_links",
        sa.Column("id",         sa.String, primary_key=True),
        sa.Column("source_id",  sa.String, sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id",  sa.String, sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label",      sa.String(100)),
        sa.Column("link_type",  sa.String(30), default="ethernet"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    for table in ["topology_links","alerts","interventions","probe_results","devices","users"]:
        op.drop_table(table)
