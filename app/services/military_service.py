from datetime import date, timedelta
import calendar
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import MilitaryEvent, MilitaryProfile
from app.utils.dates import d_day, event_end, service_progress

SERVICE_BRANCHES = {
    "ARMY": ("육군", 18),
    "MARINES": ("해병대", 18),
    "NAVY": ("해군", 20),
    "AIR_FORCE": ("공군", 21),
    "SOCIAL_SERVICE": ("사회복무요원", 21),
    "OTHER": ("기타", None),
}


def branch_label(branch: Optional[str]) -> str:
    return SERVICE_BRANCHES.get(branch, ("미등록", None))[0]


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def estimated_discharge_date(enlistment: date, service_branch: str) -> date:
    duration = SERVICE_BRANCHES.get(service_branch, ("", None))[1]
    if duration is None:
        raise ValueError("기타 군종은 전역예정일을 직접 입력해주세요.")
    # The discharge date is the last day of the stated service period.
    return add_months(enlistment, duration) - timedelta(days=1)


def upsert_profile(session: Session, guild_id: int, user_id: int, display_name: str,
                   enlistment: date, discharge: date, service_branch: str) -> MilitaryProfile:
    profile = session.scalar(select(MilitaryProfile).where(
        MilitaryProfile.guild_id == guild_id,
        MilitaryProfile.discord_user_id == user_id,
    ))
    if profile is None:
        profile = MilitaryProfile(guild_id=guild_id, discord_user_id=user_id, display_name=display_name,
                                  service_branch=service_branch, enlistment_date=enlistment, discharge_date=discharge)
        session.add(profile)
    else:
        profile.display_name = display_name
        profile.service_branch = service_branch
        profile.enlistment_date = enlistment
        profile.discharge_date = discharge
    session.flush()
    return profile


def get_profile(session: Session, guild_id: int, user_id: int) -> Optional[MilitaryProfile]:
    return session.scalar(select(MilitaryProfile).where(
        MilitaryProfile.guild_id == guild_id,
        MilitaryProfile.discord_user_id == user_id,
    ))


def profile_summary(profile: MilitaryProfile, reference: date, next_leave: Optional[MilitaryEvent] = None) -> dict:
    return {
        "display_name": profile.display_name,
        "service_branch": branch_label(profile.service_branch),
        "enlistment": profile.enlistment_date,
        "discharge": profile.discharge_date,
        "service_dday": d_day(profile.enlistment_date, reference),
        "discharge_dday": d_day(profile.discharge_date, reference),
        "progress": service_progress(profile.enlistment_date, profile.discharge_date, reference),
        "next_leave": next_leave,
    }


def next_leave_for_user(session: Session, guild_id: int, user_id: int, reference: date) -> Optional[MilitaryEvent]:
    return session.scalar(select(MilitaryEvent).where(
        MilitaryEvent.guild_id == guild_id,
        MilitaryEvent.discord_user_id == user_id,
        MilitaryEvent.event_type == "LEAVE",
        MilitaryEvent.start_date >= reference,
    ).order_by(MilitaryEvent.start_date, MilitaryEvent.id))
