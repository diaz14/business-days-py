# business-days-py

A small, dependency-free Python library for counting business days between two dates using a holiday calendar.

```python
from datetime import date
from business_days_py import BusinessDays, count_working_days

calendar = BusinessDays([date(2024, 1, 1)])
print(calendar.count(date(2024, 1, 1), date(2024, 1, 31)))  # 22
print(calendar.add_days(date(2024, 1, 2), 5))               # 2024-01-09
print(count_working_days(date(2024, 1, 2), date(2024, 1, 5)))  # 4
```

## Why this exists

The standard library `datetime` module gives you raw date arithmetic but nothing for the common question: "how many working days fall in this range, given our holiday calendar?". This library answers that with zero third-party dependencies, so it drops into constrained environments (CI containers with no network, audited codebases, lambda runtimes) without pulling in `python-dateutil` or a packaged holiday dataset.

The trade-off is that you supply the holidays. There is no built-in regional holiday table, because bundling one would mean committing to update schedules and locales this library has no business opining on. Pass a list of `datetime.date` objects and you get deterministic counts.

## Edge you will hit

The count is inclusive of both start and end dates. If you need a half-open interval `[start, end)` — common when chaining date ranges — pass `start` as one day later, or adjust the end. This choice is documented in the module docstring; it was picked because the most frequent question ("how many working days in this month?") expects the boundary days to count.

`add_days(start, 0)` returns `start` unchanged even if `start` is a weekend or holiday. It does *not* roll forward to the next business day. If you want "the next business day on or after", call `add_days(start, 0)` only when `is_business_day(start)` is true, otherwise `add_days(start, 1)`.

If `start` is after `end` in `count`, the two are swapped and the inclusive span is returned. You will never get a negative number.
