from datetime import UTC, datetime


def get_previous_month() -> str:
    """
    Return the previous month in YYYY-MM format.
    """

    today = datetime.now(UTC)

    year = today.year
    month = today.month

    if month == 1:
        return f"{year - 1}-12"

    return f"{year}-{month - 1:02d}"