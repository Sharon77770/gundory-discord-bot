from datetime import date

from app.services.calendar_service import calendar_text
from app.database.models import MilitaryEvent


def test_cross_month_event_appears_in_both_months():
    event = MilitaryEvent(id=1, guild_id=1, discord_user_id=1, event_type="LEAVE", title="연말 휴가",
                          start_date=date(2026, 12, 30), end_date=date(2027, 1, 3))
    december = calendar_text(2026, 12, [event])
    january = calendar_text(2027, 1, [event])
    assert "30*" in december and "31*" in december
    assert "01*" in january and "03*" in january
