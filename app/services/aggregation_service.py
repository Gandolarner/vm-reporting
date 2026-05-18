from app.database.connection import SessionLocal
from app.database.models import VirtualMachine
import app.database.repositories as repositories
from app.processing.aggregation import aggregate_metric_records
from app.processing.evaluation import evaluate_aggregate

import logging 

logger = logging.getLogger(__name__)


def run_monthly_aggregation(
    month: str,
) -> int:
    """
    Aggregate and evaluate all VM metrics
    for a given month.

    Returns the number of processed VMs.
    """

    logger.info("Starting monthly aggregation for month %s", month)

    year_value, month_value = month.split("-")

    year = int(year_value)
    month_number = int(month_value)

    db = SessionLocal()

    processed_vm_count = 0

    try:
        virtual_machines = (
            db.query(VirtualMachine)
            .order_by(VirtualMachine.name)
            .all()
        )

        for vm in virtual_machines:
            metric_records = (
                repositories.get_metric_records_for_vm_and_month(
                    db=db,
                    vm=vm,
                    year=year,
                    month=month_number,
                )
            )

            if not metric_records:
                continue

            aggregation_result = aggregate_metric_records(
                metric_records,
            )

            monthly_aggregate = (
                repositories.create_or_update_monthly_aggregate(
                    db=db,
                    vm=vm,
                    month=month,
                    aggregation_result=aggregation_result,
                )
            )

            evaluation = evaluate_aggregate(
                aggregation_result,
            )

            repositories.create_or_update_evaluation_result(
                db=db,
                monthly_aggregate=monthly_aggregate,
                evaluation_result=evaluation,
            )

            processed_vm_count += 1

        return processed_vm_count
    
    except Exception:
        logger.exception("Error during monthly aggregation for month %s", month)
        raise

    finally:
        db.close()
        logger.info("Finished monthly aggregation for month %s. Processed %d VMs.", month, processed_vm_count)