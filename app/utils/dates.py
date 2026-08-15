from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Tuple
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Seoul"
DATE_FORMAT = "%Y-%m-%d"


def timezone(name: str = DEFAULT_TIMEZONE) -> ZoneInfo:
    return ZoneInfo(name)


def today(tz_name: str = DEFAULT_TIMEZONE) -> date:
    return datetime.now(timezone(tz_name)).date()


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except (TypeError, ValueError) as exc:
        raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.") from exc


def validate_range(start: date, end: Optional[date]) -> None:
    if end is not None and start > end:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")


def event_end(start: date, end: Optional[date]) -> date:
    return end or start


def inclusive_days(start: date, end: Optional[date]) -> int:
    return (event_end(start, end) - start).days + 1


def d_day(target: date, reference: Optional[date] = None) -> str:
    reference = reference or today()
    diff = (target - reference).days
    return "D-Day" if diff == 0 else f"D-{diff}" if diff > 0 else f"D+{-diff}"


def service_progress(enlistment: date, discharge: date, reference: Optional[date] = None) -> float:
    total = (discharge - enlistment).days
    if total <= 0:
        return 100.0 if (reference or today()) >= discharge else 0.0
    elapsed = ((reference or today()) - enlistment).days
    return max(0.0, min(100.0, elapsed / total * 100))


def month_bounds(year: int, month: int) -> Tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def month_shift(year: int, month: int, offset: int) -> Tuple[int, int]:
    index = year * 12 + month - 1 + offset
    return index // 12, index % 12 + 1


def intervals_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> Optional[Tuple[date, date]]:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return (start, end) if start <= end else None


def merge_intervals(intervals: Iterable[Tuple[date, date]]) -> list[Tuple[date, date]]:
    ordered = sorted(intervals)
    merged: list[Tuple[date, date]] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1] + timedelta(days=1):
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

