"""initial Briar schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "military_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("discord_user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("enlistment_date", sa.Date(), nullable=False),
        sa.Column("discharge_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("guild_id", "discord_user_id", name="uq_profile_guild_user"),
    )
    op.create_index("ix_military_profiles_guild_id", "military_profiles", ["guild_id"])
    op.create_index("ix_military_profiles_discord_user_id", "military_profiles", ["discord_user_id"])
    op.create_table(
        "military_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("discord_user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_military_events_guild_id", "military_events", ["guild_id"])
    op.create_index("ix_military_events_discord_user_id", "military_events", ["discord_user_id"])
    op.create_index("ix_military_events_event_type", "military_events", ["event_type"])
    op.create_index("ix_military_events_start_date", "military_events", ["start_date"])
    op.create_table(
        "guild_settings",
        sa.Column("guild_id", sa.Integer(), primary_key=True),
        sa.Column("notification_channel_id", sa.Integer(), nullable=True),
        sa.Column("notification_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("notification_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("guild_id", "event_id", "kind", "notification_date", name="uq_notification"),
    )
    op.create_index("ix_notification_logs_guild_id", "notification_logs", ["guild_id"])


def downgrade() -> None:
    op.drop_table("notification_logs")
    op.drop_table("guild_settings")
    op.drop_index("ix_military_events_start_date", table_name="military_events")
    op.drop_index("ix_military_events_event_type", table_name="military_events")
    op.drop_index("ix_military_events_discord_user_id", table_name="military_events")
    op.drop_index("ix_military_events_guild_id", table_name="military_events")
    op.drop_table("military_events")
    op.drop_index("ix_military_profiles_discord_user_id", table_name="military_profiles")
    op.drop_index("ix_military_profiles_guild_id", table_name="military_profiles")
    op.drop_table("military_profiles")

