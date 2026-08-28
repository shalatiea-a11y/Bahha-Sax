"""Shared business rules: opening hours + slot math, used by availability.py and book.py."""

from datetime import datetime
from zoneinfo import ZoneInfo

# The shop is in Halmstad, Sweden - "past" must be judged in local time, not
# server UTC time, otherwise slots near midnight would be filtered wrong.
STOCKHOLM = ZoneInfo('Europe/Stockholm')

# Bahaa Sax real opening hours. weekday: Monday=0 ... Sunday=6.
# Value is (open, close) or None if closed that day.
HOURS = {
    0: ('11:00', '19:00'),  # Monday
    1: ('11:00', '19:00'),  # Tuesday
    2: ('11:00', '19:00'),  # Wednesday
    3: ('11:00', '19:00'),  # Thursday
    4: ('11:00', '19:00'),  # Friday
    5: ('10:00', '18:00'),  # Saturday
    6: None,                # Sunday - closed
}
SLOT_STEP_MIN = 30


def hours_for(weekday):
    """weekday: Monday=0 ... Sunday=6. Returns (open, close) or None if closed."""
    return HOURS.get(weekday)


def _to_min(hhmm):
    h, m = map(int, hhmm.split(':'))
    return h * 60 + m


def slot_list(date_obj, duration_min):
    hrs = hours_for(date_obj.weekday())
    if not hrs:
        return []
    start = _to_min(hrs[0])
    end = _to_min(hrs[1])
    slots = []
    cur = start
    while cur + duration_min <= end:
        slots.append(f'{cur // 60:02d}:{cur % 60:02d}')
        cur += SLOT_STEP_MIN
    return slots


def overlaps(a_start, a_min, b_start, b_min):
    a0 = _to_min(a_start)
    a1 = a0 + a_min
    b0 = _to_min(b_start)
    b1 = b0 + b_min
    return a0 < b1 and b0 < a1


def is_past_slot(date_obj, time_str):
    """True if this slot's start time is already behind the current time in Sweden."""
    h, m = map(int, time_str.split(':'))
    slot_dt = date_obj.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=STOCKHOLM)
    return slot_dt <= datetime.now(STOCKHOLM)
