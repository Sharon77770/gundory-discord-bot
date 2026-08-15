from datetime import date

from app.services.event_service import create_event
from app.services.military_service import next_leave_for_user
from app.services.notification_service import claim_notification
from app.utils.dates import event_end


def test_next_leave_excludes_past_events(db):
    create_event(db, 1, 10, "LEAVE", "지난 휴가", date(2026, 1, 1), date(2026, 1, 3), None)
    next_event = create_event(db, 1, 10, "LEAVE", "다음 휴가", date(2026, 12, 24), date(2026, 12, 28), None)
    db.commit()
    assert next_leave_for_user(db, 1, 10, date(2026, 12, 1)).id == next_event.id


def test_same_day_event_end_is_start(db):
    event = create_event(db, 1, 10, "OUTING", "외출", date(2026, 12, 24), None, None)
    assert event_end(event.start_date, event.end_date) == date(2026, 12, 24)


def test_notification_claim_is_idempotent(db):
    target = date(2026, 12, 23)
    assert claim_notification(db, 1, 99, "leave_eve", target) is True
    db.commit()
    assert claim_notification(db, 1, 99, "leave_eve", target) is False
