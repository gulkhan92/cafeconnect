import datetime

VALID_RANGES = {"today", "week", "month", "custom"}


class InvalidRangeError(Exception):
    pass


def resolve_range(
    range_: str, start: datetime.date | None, end: datetime.date | None
) -> tuple[datetime.datetime, datetime.datetime, datetime.date, datetime.date]:
    """Resolve a named or custom range into [start_dt, end_dt) plus the
    inclusive start/end dates used for display and day-bucketing.
    """
    if range_ not in VALID_RANGES:
        raise InvalidRangeError(f"range must be one of {sorted(VALID_RANGES)}")

    today = datetime.date.today()

    if range_ == "today":
        start_date = end_date = today
    elif range_ == "week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = today
    elif range_ == "month":
        start_date = today.replace(day=1)
        end_date = today
    else:
        if start is None or end is None:
            raise InvalidRangeError("start and end are required when range=custom")
        if start > end:
            raise InvalidRangeError("start must not be after end")
        start_date, end_date = start, end

    start_dt = datetime.datetime.combine(start_date, datetime.time.min)
    end_dt = datetime.datetime.combine(end_date + datetime.timedelta(days=1), datetime.time.min)
    return start_dt, end_dt, start_date, end_date
