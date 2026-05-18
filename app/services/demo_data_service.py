from datetime import UTC, datetime, timedelta

from app.database.connection import SessionLocal
import app.database.repositories as repositories


DEMO_VMS = [
    {
        "moid": "demo-vm-001",
        "name": "DEMO-LOW-USAGE",
        "cpu": 5.0,
        "memory": 12.0,
        "storage": 15.0,
    },
    {
        "moid": "demo-vm-002",
        "name": "DEMO-NORMAL",
        "cpu": 35.0,
        "memory": 45.0,
        "storage": 55.0,
    },
    {
        "moid": "demo-vm-003",
        "name": "DEMO-HIGH-MEMORY",
        "cpu": 40.0,
        "memory": 82.0,
        "storage": 60.0,
    },
    {
        "moid": "demo-vm-004",
        "name": "DEMO-CRITICAL-STORAGE",
        "cpu": 18.0,
        "memory": 55.0,
        "storage": 94.0,
    },
    {
        "moid": "demo-vm-005",
        "name": "DEMO-NO-STORAGE-DATA",
        "cpu": 10.0,
        "memory": 15.0,
        "storage": None,
    },
    {
        "moid": "demo-vm-006",
        "name": "DEMO-CPU-WARNING",
        "cpu": 75.0,
        "memory": 40.0,
        "storage": 50.0,
    },
    {
    "moid": "demo-vm-007",
    "name": "DEMO-WITHOUT-METRICS",
    "cpu": None,
    "memory": None,
    "storage": None,
    "create_metric_records": False,
    },
]


def seed_demo_data(
    month: str,
) -> int:
    """
    Insert demo VM metric records for a given month.

    Returns the number of created MetricRecords.
    """

    year_value, month_value = month.split("-")

    year = int(year_value)
    month_number = int(month_value)

    period_start = datetime(
        year,
        month_number,
        1,
        tzinfo=UTC,
    )

    if month_number == 12:
        period_end = datetime(
            year + 1,
            1,
            1,
            tzinfo=UTC,
        )
    else:
        period_end = datetime(
            year,
            month_number + 1,
            1,
            tzinfo=UTC,
        )

    db = SessionLocal()

    created_records = 0

    try:

        collection_run = repositories.create_collection_run(
            db=db,
            period_start=period_start,
            period_end=period_end,
        )

        for vm_data in DEMO_VMS:
            vm = repositories.create_or_update_vm(
                db=db,
                moid=vm_data["moid"],
                name=vm_data["name"],
            )

            if vm_data.get("create_metric_records", True) is False:
                continue

            for day in [1, 8, 15, 22]:
                timestamp = period_start + timedelta(
                    days=day - 1,
                    hours=12,
                )

                cpu_value = vm_data["cpu"] + (day % 3)
                memory_value = vm_data["memory"] + (day % 4)
                storage_value = vm_data["storage"]

                if storage_value is not None:
                    storage_value = storage_value + (day % 2)

                repositories.create_metric_record(
                    db=db,
                    vm=vm,
                    collection_run=collection_run,
                    timestamp=timestamp,
                    power_state="POWERED_ON",
                    cpu_usage_percent=cpu_value,
                    memory_usage_percent=memory_value,
                    storage_usage_percent=storage_value,
                )

                created_records += 1

        repositories.finish_collection_run(
            db=db,
            collection_run=collection_run,
            status="SUCCESS",
            processed_vm_count=len(DEMO_VMS),
            created_metric_record_count=created_records,
        )

        return created_records

    finally:
        db.close()