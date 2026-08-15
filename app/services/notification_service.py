from datetime import date, timedelta
import logging
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import GuildSettings, MilitaryEvent, MilitaryProfile, NotificationLog
from app.utils.dates import event_end

logger = logging.getLogger("briar.notifications")


def settings_for(session: Session, guild_id: int) -> Optional[GuildSettings]:
    return session.get(GuildSettings, guild_id)


def save_channel(session: Session, guild_id: int, channel_id: int) -> GuildSettings:
    settings = session.get(GuildSettings, guild_id)
    if settings is None:
        settings = GuildSettings(guild_id=guild_id, notification_channel_id=channel_id, notification_enabled=True)
        session.add(settings)
    else:
        settings.notification_channel_id = channel_id
    session.flush()
    return settings


def set_enabled(session: Session, guild_id: int, enabled: bool) -> GuildSettings:
    settings = session.get(GuildSettings, guild_id)
    if settings is None:
        settings = GuildSettings(guild_id=guild_id, notification_enabled=enabled)
        session.add(settings)
    else:
        settings.notification_enabled = enabled
    session.flush()
    return settings


def due_notifications(session: Session, target: date) -> List[Tuple[str, object, Optional[MilitaryProfile]]]:
    result = []
    for event in session.scalars(select(MilitaryEvent).where(MilitaryEvent.event_type == "LEAVE")):
        end = event_end(event.start_date, event.end_date)
        kind = ""
        if event.start_date == target - timedelta(days=1):
            kind = "leave_eve"
        elif event.start_date == target:
            kind = "leave_start"
        elif end == target:
            kind = "leave_end"
        if kind:
            profile = session.scalar(select(MilitaryProfile).where(
                MilitaryProfile.guild_id == event.guild_id,
                MilitaryProfile.discord_user_id == event.discord_user_id,
            ))
            result.append((kind, event, profile))
    for profile in session.scalars(select(MilitaryProfile).where(MilitaryProfile.discharge_date == target)):
        result.append(("discharge", profile, profile))
    return result


def claim_notification(session: Session, guild_id: int, event_id: Optional[int], kind: str, target: date) -> bool:
    log = NotificationLog(guild_id=guild_id, event_id=event_id, kind=kind, notification_date=target)
    session.add(log)
    try:
        session.flush()
        return True
    except IntegrityError:
        session.rollback()
        logger.info("notification already claimed guild=%s event=%s kind=%s date=%s", guild_id, event_id, kind, target)
        return False

