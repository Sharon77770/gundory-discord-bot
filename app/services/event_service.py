from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import MilitaryEvent
from app.utils.dates import event_end, validate_range

EVENT_TYPES = {
    "LEAVE": ("휴가", "🟢"),
    "OUTING": ("외출", "🔵"),
    "OVERNIGHT": ("외박", "🟣"),
    "VISIT": ("면회", "🟡"),
    "RETURN": ("복귀", "🔴"),
    "ETC": ("기타", "⚪"),
}


def type_label(event_type: str) -> str:
    return EVENT_TYPES.get(event_type, EVENT_TYPES["ETC"])[0]


def type_icon(event_type: str) -> str:
    return EVENT_TYPES.get(event_type, EVENT_TYPES["ETC"])[1]


def create_event(session: Session, guild_id: int, user_id: int, event_type: str, title: str,
                 start: date, end: Optional[date], memo: Optional[str]) -> MilitaryEvent:
    validate_range(start, end)
    if event_type not in EVENT_TYPES:
        raise ValueError("지원하지 않는 일정 종류입니다.")
    event = MilitaryEvent(guild_id=guild_id, discord_user_id=user_id, event_type=event_type,
                          title=title.strip(), start_date=start, end_date=end, memo=memo.strip() if memo else None)
    if not event.title:
        raise ValueError("일정 제목을 입력해주세요.")
    session.add(event)
    session.flush()
    return event


def list_events(session: Session, guild_id: int, user_id: int, include_past: bool, reference: date) -> List[MilitaryEvent]:
    query = select(MilitaryEvent).where(MilitaryEvent.guild_id == guild_id, MilitaryEvent.discord_user_id == user_id)
    if not include_past:
        query = query.where(MilitaryEvent.end_date.is_(None) & (MilitaryEvent.start_date >= reference) |
                            MilitaryEvent.end_date >= reference)
    return list(session.scalars(query.order_by(MilitaryEvent.start_date, MilitaryEvent.id)))


def get_owned_event(session: Session, guild_id: int, user_id: int, event_id: int) -> Optional[MilitaryEvent]:
    return session.scalar(select(MilitaryEvent).where(
        MilitaryEvent.id == event_id,
        MilitaryEvent.guild_id == guild_id,
        MilitaryEvent.discord_user_id == user_id,
    ))


def update_event(session: Session, event: MilitaryEvent, event_type: str, title: str, start: date,
                 end: Optional[date], memo: Optional[str]) -> MilitaryEvent:
    validate_range(start, end)
    if event_type not in EVENT_TYPES:
        raise ValueError("지원하지 않는 일정 종류입니다.")
    event.event_type, event.title = event_type, title.strip()
    event.start_date, event.end_date, event.memo = start, end, memo.strip() if memo else None
    if not event.title:
        raise ValueError("일정 제목을 입력해주세요.")
    session.flush()
    return event


def delete_event(session: Session, event: MilitaryEvent) -> None:
    session.delete(event)


def overlaps_month(event: MilitaryEvent, month_start: date, month_end: date) -> bool:
    return event.start_date <= month_end and event_end(event.start_date, event.end_date) >= month_start

