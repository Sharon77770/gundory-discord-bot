from calendar import monthcalendar
from datetime import date, timedelta
from typing import Iterable, List, Tuple

from app.database.models import MilitaryEvent
from app.services.event_service import overlaps_month, type_icon, type_label
from app.utils.dates import event_end, month_bounds


def calendar_text(year: int, month: int, events: Iterable[MilitaryEvent]) -> str:
    month_start, month_end = month_bounds(year, month)
    active = [event for event in events if overlaps_month(event, month_start, month_end)]
    days = {day for event in active for day in _days_in_month(event, month_start, month_end)}
    weeks = monthcalendar(year, month)
    # Keep every cell exactly three ASCII characters wide. Korean glyphs and
    # bracketed day numbers have different display widths in Discord clients.
    lines = [f"{year}-{month:02d}".center(27), "MON TUE WED THU FRI SAT SUN"]
    for week in weeks:
        cells = []
        for day in week:
            if not day:
                cells.append("   ")
            elif day in days:
                cells.append(f"{day:02d}*")
            else:
                cells.append(f"{day:02d} ")
        lines.append(" ".join(cells))
    return "```text\n" + "\n".join(lines) + "\n```\n`*` 일정 있음"


def _days_in_month(event: MilitaryEvent, month_start: date, month_end: date) -> List[int]:
    start = max(event.start_date, month_start)
    end = min(event_end(event.start_date, event.end_date), month_end)
    return [(start + timedelta(days=i)).day for i in range((end - start).days + 1)]


def month_detail_lines(events: Iterable[MilitaryEvent], display_names: dict[int, str], month_start: date, month_end: date) -> List[str]:
    lines: List[str] = []
    for event in sorted((e for e in events if overlaps_month(e, month_start, month_end)), key=lambda item: (item.start_date, item.id)):
        start = max(event.start_date, month_start)
        end = min(event_end(event.start_date, event.end_date), month_end)
        name = display_names.get(event.discord_user_id, "알 수 없는 사용자")
        date_text = start.strftime("%m/%d") if start == end else f"{start:%m/%d} ~ {end:%m/%d}"
        lines.append(f"{type_icon(event.event_type)} {name}\n{date_text} · {type_label(event.event_type)} · {event.title}")
    return lines
