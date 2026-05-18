from datetime import UTC, datetime, timedelta

from app.config.settings import settings
from app.database.connection import SessionLocal
import app.database.repositories as repositories
from app.vcenter.pyvmomi_client import PyVmomiClient
import logging

logger = logging.getLogger(__name__)


def collect_metrics_for_all_vms() -> int:
    """
    Collect VM metrics from vCenter and
    store MetricRecords in database.

    Returns the number of stored MetricRecords.
    """

    client = PyVmomiClient(
        host=settings.VCENTER_HOST,
        username=settings.VCENTER_USERNAME,
        password=settings.VCENTER_PASSWORD,
        port=settings.VCENTER_PORT,
        verify_ssl=settings.VCENTER_VERIFY_SSL,
    )

    db = SessionLocal()

    stored_metric_count = 0

    try:
        print("Connecting to vCenter...")
        logger.info("Connecting to vCenter at %s", settings.VCENTER_HOST)
        client.connect()

        print("Loading VMs...")
        logger.info("Loading VMs from vCenter")
        vms = client.get_all_vms()

        print(f"Loaded {len(vms)} VMs.")
        logger.info("Loaded %d VMs from vCenter", len(vms))

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=1)

        collection_run = repositories.create_collection_run(
            db=db,
            period_start=start_time,
            period_end=end_time,
        )

        for vm in vms:
            records = client.collect_vm_metrics(
                vm=vm,
                start_time=start_time,
                end_time=end_time,
            )

            database_vm = repositories.create_or_update_vm(
                db=db,
                moid=vm._moId,
                name=vm.name,
            )

            power_state = str(vm.runtime.powerState)

            for record in records:
                repositories.create_metric_record(
                    db=db,
                    vm=database_vm,
                    collection_run=collection_run,
                    timestamp=record["timestamp"],
                    power_state=power_state,
                    cpu_usage_percent=record[
                        "cpu_usage_percent"
                    ],
                    memory_usage_percent=record[
                        "memory_usage_percent"
                    ],
                    storage_usage_percent=record[
                        "storage_usage_percent"
                    ],
                )

                stored_metric_count += 1

        repositories.finish_collection_run(
            db=db,
            collection_run=collection_run,
            status="SUCCESS",
            processed_vm_count=len(vms),
            created_metric_record_count=stored_metric_count,
        )

        logger.info("Stored %d MetricRecords for %d VMs", stored_metric_count, len(vms))
        logger.info("Finished collection run with ID %d", collection_run.id)

        return stored_metric_count
    
    except Exception:
        logger.exception("Error during metric collection")
        raise

    finally:
        client.disconnect()
        db.close()