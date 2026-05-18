from datetime import datetime, UTC, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.processing.aggregation import aggregate_metric_records
from app.processing.evaluation import evaluate_aggregate
import app.database.models as models
import app.database.repositories as repositories


def test_full_aggregation_workflow() -> None:
    '''
    Test the full aggregation workflow, from inserting raw metric records to evaluating the aggregate.
    '''

    engine = create_engine(
        'sqlite:///:memory:',
        future=True,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(hours=1)

        measurement_time_1 = period_start + timedelta(minutes=10)
        measurement_time_2 = period_start + timedelta(minutes=20)

        vm = repositories.create_vm(
            db=db,
            moid="vm-test-001",
            name="TEST-VM-001",
        )

        collection_run = repositories.create_collection_run(
            db=db,
            period_start=period_start,
            period_end=period_end,
        )

        repositories.create_metric_record(
            db=db,
            vm=vm,
            collection_run=collection_run,
            timestamp=measurement_time_1,
            cpu_usage_percent=10.0,
            memory_usage_percent=50.0,
            storage_usage_percent=70.0,
            power_state="POWERED_ON",
        )

        repositories.create_metric_record(
            db=db,
            vm=vm,
            collection_run=collection_run,
            timestamp=measurement_time_2,
            cpu_usage_percent=30.0,
            memory_usage_percent=70.0,
            storage_usage_percent=90.0,
            power_state="POWERED_ON",
        )

        records = repositories.get_metric_records_for_vm_and_month(
            db=db,
            vm=vm,
            year=period_end.year,
            month=period_end.month,
        )

        aggregation_result = aggregate_metric_records(records)

        monthly_aggregate = repositories.create_or_update_monthly_aggregate(
            db=db,
            vm=vm,
            month=f"{period_end.year}-{period_end.month:02d}",
            aggregation_result=aggregation_result,
        )

        evaluation = evaluate_aggregate(aggregation_result)

        evaluation_result = repositories.create_or_update_evaluation_result(
            db=db,
            monthly_aggregate=monthly_aggregate,
            evaluation_result=evaluation,
        )

        finished_run = repositories.finish_collection_run(
            db=db,
            collection_run=collection_run,
            status="SUCCESS",
            processed_vm_count=1,
            created_metric_record_count=len(records),
        )

        assert isinstance(vm, models.VirtualMachine)
        assert isinstance(collection_run, models.CollectionRun)
        assert isinstance(records[0], models.MetricRecord)
        assert isinstance(monthly_aggregate, models.MonthlyAggregate)
        assert isinstance(evaluation_result, models.EvaluationResult)

        assert len(records) == 2

        assert aggregation_result["metric_record_count"] == 2
        assert monthly_aggregate.metric_record_count == 2

        assert aggregation_result["cpu_avg_percent"] == 20.0
        assert aggregation_result["cpu_min_percent"] == 10.0
        assert aggregation_result["cpu_max_percent"] == 30.0

        assert aggregation_result["memory_avg_percent"] == 60.0
        assert aggregation_result["memory_min_percent"] == 50.0
        assert aggregation_result["memory_max_percent"] == 70.0

        assert aggregation_result["storage_avg_percent"] == 80.0
        assert aggregation_result["storage_min_percent"] == 70.0
        assert aggregation_result["storage_max_percent"] == 90.0

        assert monthly_aggregate.cpu_avg_percent == 20.0
        assert monthly_aggregate.memory_avg_percent == 60.0
        assert monthly_aggregate.storage_avg_percent == 80.0

        assert evaluation_result.cpu_status == "NORMAL"
        assert evaluation_result.memory_status == "NORMAL"
        assert evaluation_result.storage_status == "WARNING"
        assert evaluation_result.overall_status == "WARNING"

        assert finished_run.status == "SUCCESS"
        assert finished_run.processed_vm_count == 1
        assert finished_run.created_metric_record_count == 2
        assert finished_run.finished_at is not None

        assert records[0].power_state == "POWERED_ON"
        assert records[1].power_state == "POWERED_ON"

    finally:
        db.close()

def test_month_boundary_separation() -> None:
    """
    Test that metric records are correctly separated
    across month and year boundaries.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        period_start = datetime(
            2025,
            12,
            31,
            7,
            0,
            tzinfo=UTC,
        )

        period_end = datetime(
            2026,
            1,
            1,
            7,
            0,
            tzinfo=UTC,
        )

        vm = repositories.create_vm(
            db=db,
            moid="vm-boundary-test",
            name="BOUNDARY-TEST-VM",
        )

        collection_run = repositories.create_collection_run(
            db=db,
            period_start=period_start,
            period_end=period_end,
        )

        repositories.create_metric_record(
            db=db,
            vm=vm,
            collection_run=collection_run,
            timestamp=datetime(
                2025,
                12,
                31,
                23,
                0,
                tzinfo=UTC,
            ),
            cpu_usage_percent=10.0,
            memory_usage_percent=20.0,
            storage_usage_percent=30.0,
            power_state="POWERED_ON",
        )

        repositories.create_metric_record(
            db=db,
            vm=vm,
            collection_run=collection_run,
            timestamp=datetime(
                2026,
                1,
                1,
                1,
                0,
                tzinfo=UTC,
            ),
            cpu_usage_percent=90.0,
            memory_usage_percent=80.0,
            storage_usage_percent=70.0,
            power_state="POWERED_ON",
        )

        december_records = repositories.get_metric_records_for_vm_and_month(
            db=db,
            vm=vm,
            year=2025,
            month=12,
        )

        january_records = repositories.get_metric_records_for_vm_and_month(
            db=db,
            vm=vm,
            year=2026,
            month=1,
        )

        assert len(december_records) == 1
        assert len(january_records) == 1

        assert december_records[0].cpu_usage_percent == 10.0
        assert january_records[0].cpu_usage_percent == 90.0

    finally:
        db.close()