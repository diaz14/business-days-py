"""Tests for business_days_py.core.

Every test uses explicit, fixed dates. No test depends on the current wall
clock. Holidays are passed as plain datetime.date objects so the assertions
are fully deterministic.
"""

import unittest
from datetime import date

from business_days_py.core import BusinessDays, count_working_days


class TestBusinessDays(unittest.TestCase):
    def test_single_business_day_is_one(self):
        # 2024-01-02 is a Tuesday and not a holiday.
        bd = BusinessDays()
        self.assertEqual(bd.count(date(2024, 1, 2), date(2024, 1, 2)), 1)

    def test_single_weekend_day_is_zero(self):
        # 2024-01-06 is a Saturday.
        bd = BusinessDays()
        self.assertEqual(bd.count(date(2024, 1, 6), date(2024, 1, 6)), 0)

    def test_single_holiday_is_zero(self):
        holiday = date(2024, 1, 1)
        bd = BusinessDays([holiday])
        self.assertEqual(bd.count(holiday, holiday), 0)

    def test_full_week_no_holidays(self):
        # Monday 2024-01-01 through Sunday 2024-01-07: Mon-Fri inclusive = 5.
        # Note 2024-01-01 is also a holiday in many calendars, but here we pass
        # no holidays so only the weekend is excluded.
        bd = BusinessDays()
        self.assertEqual(bd.count(date(2024, 1, 1), date(2024, 1, 7)), 5)

    def test_holiday_inside_range_is_skipped(self):
        # Tuesday 2024-01-02 through Friday 2024-01-05 = 4 weekdays normally.
        # Make Wednesday 2024-01-03 a holiday: expect 3.
        holidays = [date(2024, 1, 3)]
        bd = BusinessDays(holidays)
        self.assertEqual(bd.count(date(2024, 1, 2), date(2024, 1, 5)), 3)

    def test_swapped_start_end(self):
        # If start > end, the span is still counted inclusively.
        bd = BusinessDays()
        forward = bd.count(date(2024, 1, 2), date(2024, 1, 4))
        backward = bd.count(date(2024, 1, 4), date(2024, 1, 2))
        self.assertEqual(forward, backward)
        self.assertEqual(forward, 3)  # Tue, Wed, Thu

    def test_weekend_only_range(self):
        # Saturday and Sunday only -> 0 business days.
        bd = BusinessDays()
        self.assertEqual(bd.count(date(2024, 1, 6), date(2024, 1, 7)), 0)

    def test_is_business_day_for_weekday(self):
        bd = BusinessDays()
        self.assertTrue(bd.is_business_day(date(2024, 1, 3)))  # Wednesday

    def test_is_business_day_for_weekend(self):
        bd = BusinessDays()
        self.assertFalse(bd.is_business_day(date(2024, 1, 6)))  # Saturday

    def test_is_business_day_for_holiday(self):
        holiday = date(2024, 1, 1)
        bd = BusinessDays([holiday])
        self.assertFalse(bd.is_business_day(holiday))

    def test_add_days_positive(self):
        # From Monday 2024-01-01 (a weekday with no holidays here), +3
        # business days lands on Thursday 2024-01-04.
        bd = BusinessDays()
        self.assertEqual(bd.add_days(date(2024, 1, 1), 3), date(2024, 1, 4))

    def test_add_days_skips_weekend(self):
        # Friday 2024-01-05 + 1 business day = Monday 2024-01-08.
        bd = BusinessDays()
        self.assertEqual(bd.add_days(date(2024, 1, 5), 1), date(2024, 1, 8))

    def test_add_days_skips_holiday(self):
        # Tuesday 2024-01-02 +1 business day, but Wednesday 2024-01-03 is a
        # holiday, so the result is Thursday 2024-01-04.
        bd = BusinessDays([date(2024, 1, 3)])
        self.assertEqual(bd.add_days(date(2024, 1, 2), 1), date(2024, 1, 4))

    def test_add_days_negative(self):
        # Friday 2024-01-05 - 1 business day = Thursday 2024-01-04.
        bd = BusinessDays()
        self.assertEqual(bd.add_days(date(2024, 1, 5), -1), date(2024, 1, 4))

    def test_add_days_zero_returns_start(self):
        # Adding 0 business days returns start unchanged, even if start is a
        # weekend. This is the documented behaviour: "add zero working days"
        # rather than rolling forward.
        bd = BusinessDays()
        saturday = date(2024, 1, 6)
        self.assertEqual(bd.add_days(saturday, 0), saturday)

    def test_convenience_function_matches_class(self):
        holidays = [date(2024, 1, 3)]
        bd = BusinessDays(holidays)
        self.assertEqual(
            count_working_days(date(2024, 1, 2), date(2024, 1, 5), holidays),
            bd.count(date(2024, 1, 2), date(2024, 1, 5)),
        )

    def test_holiday_set_is_immutable_after_construction(self):
        # Mutating the original list must not affect the calendar, because the
        # constructor copies into a frozenset.
        original = [date(2024, 1, 3)]
        bd = BusinessDays(original)
        original.append(date(2024, 1, 4))
        # Wednesday 2024-01-03 is still a holiday, Thursday 2024-01-04 is not.
        self.assertFalse(bd.is_business_day(date(2024, 1, 3)))
        self.assertTrue(bd.is_business_day(date(2024, 1, 4)))

    def test_datetime_passed_as_holiday_is_coerced(self):
        # Passing a datetime.datetime instead of date should still work
        # because the constructor reads year/month/day attributes.
        import datetime
        dt_holiday = datetime.datetime(2024, 1, 3, 12, 0, 0)
        bd = BusinessDays([dt_holiday])
        self.assertFalse(bd.is_business_day(date(2024, 1, 3)))

    def test_empty_holidays(self):
        # Passing an empty list is equivalent to no holidays.
        bd = BusinessDays([])
        self.assertEqual(bd.count(date(2024, 1, 2), date(2024, 1, 4)), 3)

    def test_none_holidays(self):
        # Passing None explicitly is equivalent to no holidays.
        bd = BusinessDays(None)
        self.assertEqual(bd.count(date(2024, 1, 2), date(2024, 1, 4)), 3)

    def test_same_day_non_business_returns_zero(self):
        bd = BusinessDays()
        self.assertEqual(bd.count(date(2024, 1, 7), date(2024, 1, 7)), 0)  # Sunday

    def test_long_range_with_holidays_and_weekends(self):
        # All of January 2024. Weekdays in Jan 2024: 23. Subtract 2 holidays
        # (Jan 1 and Jan 15, both weekdays) = 21.
        holidays = [date(2024, 1, 1), date(2024, 1, 15)]
        bd = BusinessDays(holidays)
        result = bd.count(date(2024, 1, 1), date(2024, 1, 31))
        self.assertEqual(result, 21)


if __name__ == "__main__":
    unittest.main()
