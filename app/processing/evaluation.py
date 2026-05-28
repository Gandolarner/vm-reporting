from app.config.threshold_loader import load_thresholds


def evaluate_usage(
    value: float | None,
    thresholds: dict,
) -> str | None:
    """
    Evaluate a usage value against thresholds and return the evaluation result.
    """

    if value is None:
        return None

    if value < thresholds["underutilized_below"]:
        return "UNDERUTILIZED"
    
    if value >= thresholds["critical_above"]:
        return "CRITICAL"
    
    if value >= thresholds["warning_above"]:
        return "WARNING"
    
    return "NORMAL"
    
def determine_overall_status(
    cpu_status: str | None,
    memory_status: str | None,
    storage_status: str | None,
) -> str:
    """
    Determine the overall status based on the most relevant individual status.
    """

    statuses = [
        status
        for status in [
            cpu_status,
            memory_status,
            storage_status,
        ]
        if status is not None
    ]

    if "CRITICAL" in statuses:
        return "CRITICAL"
    
    if "WARNING" in statuses:
        return "WARNING"
    
    if all(status == "UNDERUTILIZED" for status in statuses):
        return "UNDERUTILIZED"
    
    return "NORMAL"
    
def evaluate_aggregate(
        aggregation_result: dict[str, float],
) -> dict[str, str | None]:
    """
    Evaluate aggregated metric values for CPU, memory and storage.
    """
    thresholds = load_thresholds()

    cpu_status = evaluate_usage(aggregation_result["cpu_avg_percent"], thresholds["cpu"])
    memory_status = evaluate_usage(aggregation_result["memory_avg_percent"], thresholds["memory"])
    storage_status = evaluate_usage(aggregation_result["storage_avg_percent"], thresholds["storage"])

    overall_status = determine_overall_status(cpu_status, memory_status, storage_status)

    return {
        "cpu_status": cpu_status,
        "memory_status": memory_status,
        "storage_status": storage_status,
        "overall_status": overall_status,
    }
