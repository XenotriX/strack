from datetime import datetime, date


def round_time(dt: datetime) -> datetime:
    if dt.minute < 30:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    else:
        dt = dt.replace(minute=30, second=0, microsecond=0)
    return dt


def is_this_week(dt):
    # Get the ISO calendar year, week number of the input datetime
    year, week, _ = dt.isocalendar()

    # Get the ISO calendar year, week number of the current date
    today_year, today_week, _ = date.today().isocalendar()

    # Check if the input datetime is from the same week as the current date
    return year == today_year and week == today_week


def format_duration(seconds):
    seconds = round(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}"
