import datetime
from zoneinfo import ZoneInfo

MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def parse_birthday(text: str) -> tuple[int, int]:
    """Parse a birthday string in DD.MM format. Returns (day, month).

    Raises ValueError on invalid input.
    """
    text = text.strip()
    if "." not in text:
        raise ValueError("Please use DD.MM format (e.g. 15.06)")

    parts = text.split(".")
    if len(parts) != 2:
        raise ValueError("Please use DD.MM format (e.g. 15.06)")

    try:
        day = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise ValueError("Day and month must be numbers (e.g. 15.06)")

    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")

    # Validate day using a leap year (2000) to allow Feb 29
    try:
        datetime.date(2000, month, day)
    except ValueError:
        raise ValueError(f"Invalid day {day} for {month_name(month)}")

    return day, month


def month_name(month: int) -> str:
    """Return the English name of the month (1-12)."""
    return MONTH_NAMES[month]


def format_birthday(day: int, month: int) -> str:
    """Format a birthday as 'DD MonthName' (e.g. '15 June')."""
    return f"{day} {month_name(month)}"


def today_in_timezone(tz_name: str) -> tuple[int, int]:
    """Return today's (day, month) in the given timezone."""
    now = datetime.datetime.now(ZoneInfo(tz_name))
    return now.day, now.month
