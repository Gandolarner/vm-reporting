from app.collectors.metric_collector import collect_metrics_for_all_vms


def run_metric_collection() -> int:
    """
    Run VM metric collection.

    Returns the number of stored metric records.
    """

    return collect_metrics_for_all_vms()