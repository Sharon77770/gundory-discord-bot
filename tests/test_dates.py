from datetime import date

import pytest

from app.utils.dates import parse_date, service_progress, validate_range
from app.services.military_service import estimated_discharge_date


def test_invalid_date_is_user_friendly():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_date("2026-02-30")


def test_start_after_end_is_rejected():
    with pytest.raises(ValueError):
        validate_range(date(2026, 12, 28), date(2026, 12, 24))


def test_progress_is_clamped_before_during_after_service():
    enlistment, discharge = date(2026, 1, 1), date(2027, 1, 1)
    assert service_progress(enlistment, discharge, date(2025, 12, 1)) == 0
    assert 49 < service_progress(enlistment, discharge, date(2026, 7, 2)) < 51
    assert service_progress(enlistment, discharge, date(2027, 2, 1)) == 100


def test_discharge_estimate_uses_branch_service_months():
    enlistment = date(2026, 10, 13)
    assert estimated_discharge_date(enlistment, "ARMY") == date(2028, 4, 12)
    assert estimated_discharge_date(enlistment, "NAVY") == date(2028, 6, 12)
    assert estimated_discharge_date(enlistment, "AIR_FORCE") == date(2028, 7, 12)
