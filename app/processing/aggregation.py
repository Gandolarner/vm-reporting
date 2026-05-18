from app.database.models import MetricRecord


def filter_none_values(
    values: list[float | None],
) -> list[float]:
    """
    Remove None values from a list.
    """

    return [
        value
        for value in values
        if value is not None
    ]

def calc_avg(
    values: list[float | None],
) -> float | None:
    """
    Calculate the arithmetic mean
    of a list of values.
    """

    filtered_values = filter_none_values(
        values,
    )

    if not filtered_values:
        return None

    return (
        sum(filtered_values)
        / len(filtered_values)
    )

def calc_min(
    values: list[float | None],
) -> float | None:
    """
    Return the minimum value.
    """

    filtered_values = filter_none_values(
        values,
    )

    if not filtered_values:
        return None

    return min(filtered_values)

def calc_max(
    values: list[float | None],
) -> float | None:
    """
    Return the maximum value.
    """

    filtered_values = filter_none_values(
        values,
    )

    if not filtered_values:
        return None

    return max(filtered_values)

def aggregate_metric_records(
    metric_records: list[MetricRecord],
) -> dict:
    """
    Aggregate MetricRecords into
    monthly utilization statistics.
    """

    cpu_values = [
        record.cpu_usage_percent
        for record in metric_records
    ]

    memory_values = [
        record.memory_usage_percent
        for record in metric_records
    ]

    storage_values = [
        record.storage_usage_percent
        for record in metric_records
    ]

    return {
        "metric_record_count": len(
            metric_records
        ),
        "cpu_avg_percent": calc_avg(
            cpu_values,
        ),
        "cpu_min_percent": calc_min(
            cpu_values,
        ),
        "cpu_max_percent": calc_max(
            cpu_values,
        ),
        "memory_avg_percent": calc_avg(
            memory_values,
        ),
        "memory_min_percent": calc_min(
            memory_values,
        ),
        "memory_max_percent": calc_max(
            memory_values,
        ),
        "storage_avg_percent": calc_avg(
            storage_values,
        ),
        "storage_min_percent": calc_min(
            storage_values,
        ),
        "storage_max_percent": calc_max(
            storage_values,
        ),
    }