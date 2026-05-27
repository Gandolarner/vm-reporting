from pathlib import Path

from app.database.connection import SessionLocal
from app.database.models import MonthlyAggregate, EvaluationResult, VirtualMachine
from app.reporting.html_report import generate_html_report

import logging

logger = logging.getLogger(__name__)

def create_monthly_report(
    month: str,
) -> Path | None:
    """
    Create a monthly HTML report.

    Returns the report path or None
    if no data exists.
    """

    logger.info("Generating monthly report for month %s", month)

    db = SessionLocal()
    report_path: Path | None = None

    try:
        results = (
            db.query(
                MonthlyAggregate,
                VirtualMachine,
                EvaluationResult,
            )
            .join(
                VirtualMachine,
                MonthlyAggregate.vm_id
                == VirtualMachine.id,
            )
            .join(
                EvaluationResult,
                EvaluationResult.monthly_aggregate_id
                == MonthlyAggregate.id,
            )
            .filter(
                MonthlyAggregate.month == month,
            )
            .order_by(
                VirtualMachine.name,
            )
            .all()
        )

        if not results:
            logger.warning("No data found for month %s. Report will not be generated.", month)
            return None
        
        all_vms = (
            db.query(VirtualMachine)
            .order_by(VirtualMachine.name)
            .all()
        )

        vm_ids_with_aggregates = {
            aggregate.vm_id
            for aggregate, _, _ in results
        }

        vms_without_metrics = [
            vm
            for vm in all_vms
            if vm.id not in vm_ids_with_aggregates
        ]


        report_path = generate_html_report(
            month=month,
            results=results,
            inventory_vm_count=len(all_vms),
            vms_without_metrics=vms_without_metrics,
        )

        return report_path
    
    except Exception:
        logger.exception("Failed to generate monthly report for month %s.", month)
        raise

    finally:
        db.close()

        if report_path is None:
            logger.info(
                "Finished report command for month %s without creating a report.",
                month,
            )
        else:
            logger.info(
                "Finished generating monthly report for month %s at %s",
                month,
                report_path,
            )