from datetime import date

from app.bot.cogs.special import find_overlapping_leaves


def test_leave_overlap_uses_real_interval_intersection(event_factory):
    events = [
        event_factory(10, date(2026, 12, 24), date(2026, 12, 28)),
        event_factory(20, date(2026, 12, 26), date(2026, 12, 30)),
    ]
    result = find_overlapping_leaves(events)
    assert result == [(date(2026, 12, 26), date(2026, 12, 28), {10, 20})]


def test_multiple_overlap_segments_are_all_returned(event_factory):
    events = [
        event_factory(10, date(2026, 12, 24), date(2026, 12, 26)),
        event_factory(20, date(2026, 12, 25), date(2026, 12, 27)),
        event_factory(30, date(2026, 12, 26), date(2026, 12, 28)),
    ]
    result = find_overlapping_leaves(events)
    assert result[0] == (date(2026, 12, 25), date(2026, 12, 25), {10, 20})
    assert result[1] == (date(2026, 12, 26), date(2026, 12, 26), {10, 20, 30})
    assert result[2] == (date(2026, 12, 27), date(2026, 12, 27), {20, 30})

