from pathlib import Path
from app.services.aggregation_service import run_monthly_aggregation
from app.services.reporting_service import create_monthly_report
from app.services.collection_service import run_metric_collection
from app.utils.date_utils import get_previous_month

import logging

logger = logging.getLogger(__name__)


def run_monthly_workflow() -> tuple[
    str,
    int,
    Path | None,
]:
    """
    Run the monthly reporting workflow.

    Returns:
        (
            month,
            processed_vm_count,
            report_path,
        )
    """

    logger.info("Starting monthly workflow")

    month = get_previous_month()

    logger.info("Previous month determined as %s", month)

    processed_vm_count = run_monthly_aggregation(month)
    
    logger.info("Monthly aggregation completed for month %s. Processed %d VMs.", month, processed_vm_count)

    if processed_vm_count == 0:

        logger.warning("No metric records found for month %s. Report will not be generated.", month)

        return month, 0, None

    report_path = create_monthly_report(month)

    logger.info("Monthly report generation completed for month %s. Report path: %s", month, report_path)

    return month, processed_vm_count, report_path


def run_daily_workflow() -> int:
    """
    Run the daily metric collection workflow.
    """

    logger.info("Starting daily workflow.")

    stored_record_count = run_metric_collection()

    logger.info("Finished daily workflow. Stored %d MetricRecords.", stored_record_count)

    return stored_record_count