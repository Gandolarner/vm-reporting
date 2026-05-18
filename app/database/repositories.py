from datetime import UTC, datetime
from sqlalchemy import extract
from sqlalchemy.orm import Session
from app.database.models import CollectionRun, EvaluationResult, MetricRecord, VirtualMachine, MonthlyAggregate


def get_vm_by_moid(
    db: Session,
    moid: str,
) -> VirtualMachine | None:
    """
    Get a virtual machine by its MOID.
    """

    return (
        db.query(VirtualMachine).filter(VirtualMachine.moid == moid).first()
    )

def create_vm(
    db: Session,
    moid: str,
    name: str,
) -> VirtualMachine:
    """
    Create and persist a new virtual machine.
    """

    vm = VirtualMachine(moid=moid, name=name,)

    db.add(vm)
    db.commit()
    db.refresh(vm)

    return vm

def create_collection_run(
    db: Session,
    period_start: datetime,
    period_end: datetime,
    status: str = "RUNNING",
) -> CollectionRun:
    """
    Create a new collection run for a defined period.
    """

    run = CollectionRun(period_start=period_start, period_end=period_end, status=status,)

    db.add(run)
    db.commit()
    db.refresh(run)

    return run

def finish_collection_run(
    db: Session,
    collection_run: CollectionRun,
    status: str,
    processed_vm_count: int,
    created_metric_record_count: int,
    error_message: str | None = None,
) -> CollectionRun:
    """
    Finish a collection run and persist its final status.
    """

    collection_run.finished_at = datetime.now(UTC)
    collection_run.status = status
    collection_run.processed_vm_count = processed_vm_count
    collection_run.created_metric_record_count = created_metric_record_count
    collection_run.error_message = error_message

    db.commit()
    db.refresh(collection_run)

    return collection_run

def create_metric_record(
    db: Session,
    vm: VirtualMachine,
    collection_run: CollectionRun,
    power_state: str,
    timestamp: datetime,
    cpu_usage_percent: float | None = None,
    memory_usage_percent: float | None = None,
    storage_usage_percent: float | None = None,
) -> MetricRecord:
    """
    Create and persist a metric record for a virtual machine.
    """

    metric_record = MetricRecord(
        vm_id=vm.id,
        collection_run_id=collection_run.id,
        cpu_usage_percent=cpu_usage_percent,
        memory_usage_percent=memory_usage_percent,
        storage_usage_percent=storage_usage_percent,
        power_state=power_state,
        timestamp=timestamp,
    )
    db.add(metric_record)
    db.commit()
    db.refresh(metric_record)

    return metric_record

def get_metric_records_for_vm_and_month(
    db: Session,
    vm: VirtualMachine,
    year: int,
    month: int,
) -> list[MetricRecord]:
    """
    Get all metric records for a given virtual machine within a specific year and month.
    """

    return (
        db.query(MetricRecord)
        .filter(
            MetricRecord.vm_id == vm.id,
            extract("year", MetricRecord.timestamp) == year,
            extract("month", MetricRecord.timestamp) == month,
        )
        .all()
    )

def create_or_update_monthly_aggregate(
    db: Session,
    vm: VirtualMachine,
    month: str,
    aggregation_result: dict[str, float],
) -> MonthlyAggregate:
    """
    Create or update a monthly aggregate for a VM and month.

    Existing aggregates are only updated if calculated values changed.
    """

    aggregate = get_monthly_aggregate_by_vm_and_month(
        db=db,
        vm=vm,
        month=month,
    )

    if aggregate is None:
        aggregate = MonthlyAggregate(
            vm_id=vm.id,
            month=month,
            metric_record_count=aggregation_result["metric_record_count"],
            cpu_avg_percent=aggregation_result["cpu_avg_percent"],
            cpu_min_percent=aggregation_result["cpu_min_percent"],
            cpu_max_percent=aggregation_result["cpu_max_percent"],
            memory_avg_percent=aggregation_result["memory_avg_percent"],
            memory_min_percent=aggregation_result["memory_min_percent"],
            memory_max_percent=aggregation_result["memory_max_percent"],
            storage_avg_percent=aggregation_result["storage_avg_percent"],
            storage_min_percent=aggregation_result["storage_min_percent"],
            storage_max_percent=aggregation_result["storage_max_percent"],
        )

        db.add(aggregate)
        db.commit()
        db.refresh(aggregate)

        return aggregate

    fields_to_update = {
        "metric_record_count": aggregation_result["metric_record_count"],
        "cpu_avg_percent": aggregation_result["cpu_avg_percent"],
        "cpu_min_percent": aggregation_result["cpu_min_percent"],
        "cpu_max_percent": aggregation_result["cpu_max_percent"],
        "memory_avg_percent": aggregation_result["memory_avg_percent"],
        "memory_min_percent": aggregation_result["memory_min_percent"],
        "memory_max_percent": aggregation_result["memory_max_percent"],
        "storage_avg_percent": aggregation_result["storage_avg_percent"],
        "storage_min_percent": aggregation_result["storage_min_percent"],
        "storage_max_percent": aggregation_result["storage_max_percent"],
    }

    has_changes = False

    for field_name, new_value in fields_to_update.items():
        current_value = getattr(aggregate, field_name)

        if current_value != new_value:
            setattr(aggregate, field_name, new_value)
            has_changes = True

    if has_changes:
        aggregate.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(aggregate)

    return aggregate

def create_or_update_evaluation_result(
    db: Session,
    monthly_aggregate: MonthlyAggregate,
    evaluation_result: dict[str, str],
    note: str | None = None,
) -> EvaluationResult:
    """
    Create or update an evaluation result.
    """

    result = get_evaluation_result_by_monthly_aggregate(
        db=db,
        monthly_aggregate=monthly_aggregate,
    )

    if result is None:
        result = EvaluationResult(
            monthly_aggregate_id=monthly_aggregate.id,
        )

        db.add(result)

    fields_to_update = {
        "overall_status": evaluation_result["overall_status"],
        "cpu_status": evaluation_result["cpu_status"],
        "memory_status": evaluation_result["memory_status"],
        "storage_status": evaluation_result["storage_status"],
        "note": note,
    }

    has_changes = False

    for field_name, new_value in fields_to_update.items():
        current_value = getattr(result, field_name)

        if current_value != new_value:
            setattr(result, field_name, new_value)
            has_changes = True

    if has_changes:
        result.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(result)

    return result

def get_all_vms(db: Session) -> list[VirtualMachine]:
    """
    Get all virtual machines from the database.
    """

    return db.query(VirtualMachine).all()

def get_monthly_aggregate_by_vm_and_month(
    db: Session,
    vm: VirtualMachine,
    month: str,
) -> MonthlyAggregate | None:
    """
    Return the monthly aggregate for a VM and month if it exists.
    """

    return (
        db.query(MonthlyAggregate)
        .filter(MonthlyAggregate.vm_id == vm.id)
        .filter(MonthlyAggregate.month == month)
        .first()
    )

def get_evaluation_result_by_monthly_aggregate(
    db: Session,
    monthly_aggregate: MonthlyAggregate,
) -> EvaluationResult | None:
    """
    Return the evaluation result for a monthly aggregate if it exists.
    """

    return (
        db.query(EvaluationResult)
        .filter(
            EvaluationResult.monthly_aggregate_id
            == monthly_aggregate.id
        )
        .first()
    )

def create_or_update_vm(
    db: Session,
    moid: str,
    name: str,
) -> VirtualMachine:
    """
    Create or update a virtual machine.
    """

    vm = get_vm_by_moid(
        db=db,
        moid=moid,
    )

    if vm is None:
        vm = VirtualMachine(
            moid=moid,
            name=name,
        )

        db.add(vm)
        db.commit()
        db.refresh(vm)

        return vm

    if vm.name != name:
        vm.name = name

        db.commit()
        db.refresh(vm)

    return vm