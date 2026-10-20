"""Core business-day counting logic.

A "business day" here is Monday through Friday that is not present in a
user-supplied holiday calendar. Weekends are excluded unconditionally because
the most common business-day question is "how many working days fall between
these two dates?" and that question assumes a Monday-Friday week.

The implementation is deliberately small and dependency-free. It uses pure
datetime.date arithmetic so results are deterministic regardless of locale or
system timezone configuration, which matters for CI environments that may be
set to UTC.

Interpretation choice (stated plainly so callers know what they get):
- The interval is inclusive of both the start and end dates when they are
  themselves business days. A common alternative is half-open [start, end),
  but inclusive is the more intuitive default for questions like "how many
  working days are in this month?". If you need half-open, pass start + 1 day.
- Holidays are matched by exact date equality; time-of-day is ignored because
  date objects carry no time component. Callers should supply datetime.date
  values (or date-like objects with a matching interface).
- If start is after end, the two are swapped and the inclusive count is
  returned. This avoids surprising negative numbers for what is, semantically,
  still a span of days.
"""

from __future__ import annotations

from datetime import date, timedelta

__all__ = ["BusinessDays", "count_working_days"]


class BusinessDays:
    """Count working days between dates using a holiday calendar.

    The holiday set is normalized into a frozenset of date objects at
    construction time. Normalizing here (rather than per-call) means repeated
    counts over the same calendar are cheap, and the calendar is effectively
    immutable after construction which prevents accidental mutation by callers
    holding a reference to the original list.
    """

    def __init__(self, holidays=None):
        # type: (object) -> None
        """Build a calendar from an iterable of date-like objects.

        We iterate defensively rather than requiring a specific collection
        type: a list, tuple, or set all work. Each element is coerced via
        the date constructor so callers may pass datetime objects (whose
        date() is implicitly compatible) without manual conversion.
        """
        normalized = set()
        if holidays is not None:
            for h in holidays:
                # date(some_datetime) returns the date component; date(date)
                # returns the same date. This keeps the API forgiving without
                # pulling in type checks that would require isinstance.
                normalized.add(date(h.year, h.month, h.day))
        self._holidays = frozenset(normalized)

    def is_business_day(self, d):
        # type: (date) -> bool
        """Return True if *d* is a weekday and not in the holiday calendar."""
        # date.weekday(): Monday=0 .. Sunday=6. Saturday(5) and Sunday(6) are
        # excluded. Using weekday() rather than isoweekday() avoids the
        # Sunday=7 case and keeps the comparison a simple >= 5.
        if d.weekday() >= 5:
            return False
        if d in self._holidays:
            return False
        return True

    def count(self, start, end):
        # type: (date, date) -> int
        """Return the inclusive count of business days between start and end.

        If start is after end they are swapped, so the result is always a
        non-negative count of the days in the span.
        """
        if start > end:
            start, end = end, start
        total = 0
        current = start
        # Iterate day by day. For the typical ranges this library targets
        # (weeks to a few years) this linear scan is clear and fast enough;
        # a closed-form weekday formula would be error-prone around holiday
        # edge cases and harder to audit.
        while current <= end:
            if self.is_business_day(current):
                total += 1
            current = current + timedelta(days=1)
        return total

    def add_days(self, start, days):
        # type: (date, int) -> date
        """Return the date that is *days* business days from *start*.

        Positive *days* moves forward, negative moves backward. A value of 0
        returns *start* unchanged even if it is not a business day, which
        matches the principle of "add zero working days" rather than rolling
        to the next business day.
        """
        if days == 0:
            return start
        step = 1 if days > 0 else -1
        remaining = abs(days)
        current = start
        while remaining > 0:
            current = current + timedelta(days=step)
            if self.is_business_day(current):
                remaining -= 1
        return current


def count_working_days(start, end, holidays=None):
    # type: (date, date, object) -> int
    """Convenience function: build a calendar and count in one call.

    Useful for one-off calculations. If you need to query the same holiday
    calendar many times, construct a BusinessDays instance once and call its
    count method to avoid rebuilding the set each time.
    """
    return BusinessDays(holidays).count(start, end)
