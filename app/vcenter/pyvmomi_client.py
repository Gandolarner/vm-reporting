import ssl
from datetime import datetime

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim

from app.processing.storage_usage import calculate_storage_usage_percent

import logging

logger = logging.getLogger(__name__)

class PyVmomiClient:
    """
    VMware vCenter client based on pyVmomi.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        verify_ssl: bool = False,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl

        self.service_instance = None

    def connect(self) -> None:
        """
        Connect to vCenter.
        """

        ssl_context = None

        if not self.verify_ssl:
            ssl_context = ssl._create_unverified_context()

        self.service_instance = SmartConnect(
            host=self.host,
            user=self.username,
            pwd=self.password,
            port=self.port,
            sslContext=ssl_context,
        )

        logger.info("Successfully connected to vCenter at %s", self.host)

    def disconnect(self) -> None:
        """
        Disconnect from vCenter.
        """

        if self.service_instance is not None:
            Disconnect(self.service_instance)
            self.service_instance = None
            logger.info("Disconnected from vCenter at %s", self.host)

    def get_content(self):
        """
        Return vCenter inventory content.
        """

        if self.service_instance is None:
            raise RuntimeError(
                "Client is not connected."
            )

        return self.service_instance.RetrieveContent()

    def get_all_vms(self) -> list[vim.VirtualMachine]:
        """
        Return all virtual machines.
        """

        content = self.get_content()

        container_view = content.viewManager.CreateContainerView(
            content.rootFolder,
            [vim.VirtualMachine],
            True,
        )

        try:
            return list(container_view.view)
        finally:
            container_view.Destroy()

    def get_vm_inventory(self) -> list[dict]:
        """
        Return normalized VM inventory data.
        """

        virtual_machines = self.get_all_vms()

        inventory = []

        for vm in virtual_machines:
            inventory.append(
                {
                    "moid": vm._moId,
                    "name": vm.name,
                    "power_state": str(vm.runtime.powerState),
                    "cpu_count": vm.config.hardware.numCPU,
                    "memory_size_mib": vm.config.hardware.memoryMB,
                }
            )

        return inventory

    def get_performance_counters(self) -> list:
        """
        Return all available performance counters.
        """

        content = self.get_content()

        return content.perfManager.perfCounter

    def find_counter_id(
        self,
        group: str,
        name: str,
        rollup: str,
    ) -> int:
        """
        Find a performance counter ID.
        """

        counters = self.get_performance_counters()

        for counter in counters:
            if (
                counter.groupInfo.key == group
                and counter.nameInfo.key == name
                and str(counter.rollupType) == rollup
            ):
                return counter.key

        raise ValueError(
            f"Counter not found: "
            f"{group}.{name}.{rollup}"
        )

    def get_counter_unit(
        self,
        group: str,
        name: str,
        rollup: str,
    ) -> str:
        """
        Return the unit key of a counter.
        """

        counters = self.get_performance_counters()

        for counter in counters:
            if (
                counter.groupInfo.key == group
                and counter.nameInfo.key == name
                and str(counter.rollupType) == rollup
            ):
                return counter.unitInfo.key

        raise ValueError(
            f"Counter unit not found: "
            f"{group}.{name}.{rollup}"
        )

    def query_metric_values(
        self,
        vm,
        group: str,
        name: str,
        rollup: str,
        start_time: datetime,
        end_time: datetime,
        interval_id: int = 300,
    ) -> list[dict]:
        """
        Query historical metric values for a VM.
        """

        content = self.get_content()
        perf_manager = content.perfManager

        counter_id = self.find_counter_id(
            group=group,
            name=name,
            rollup=rollup,
        )

        unit_key = self.get_counter_unit(
            group=group,
            name=name,
            rollup=rollup,
        )

        metric_id = vim.PerformanceManager.MetricId(
            counterId=counter_id,
            instance="",
        )

        query = vim.PerformanceManager.QuerySpec(
            entity=vm,
            metricId=[metric_id],
            startTime=start_time,
            endTime=end_time,
            intervalId=interval_id,
        )

        results = perf_manager.QueryPerf(
            querySpec=[query],
        )

        normalized_results = []

        if not results:
            return normalized_results

        entity_metric = results[0]

        if not entity_metric.value:
            return normalized_results

        metric_series = entity_metric.value[0]

        timestamps = entity_metric.sampleInfo
        values = metric_series.value

        for timestamp_info, raw_value in zip(
            timestamps,
            values,
        ):
            value = raw_value

            if unit_key == "percent":
                value = raw_value / 100

            normalized_results.append(
                {
                    "timestamp": timestamp_info.timestamp,
                    "value": value,
                }
            )

        return normalized_results

    def collect_vm_metrics(
        self,
        vm,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:
        """
        Collect normalized VM metric records.
        """

        cpu_results = self.query_metric_values(
            vm=vm,
            group="cpu",
            name="usage",
            rollup="average",
            start_time=start_time,
            end_time=end_time,
        )

        memory_results = self.query_metric_values(
            vm=vm,
            group="mem",
            name="usage",
            rollup="average",
            start_time=start_time,
            end_time=end_time,
        )

        guest_disks = self.get_vm_guest_disks(
            vm,
        )

        storage_usage_percent = (
            calculate_storage_usage_percent(
                guest_disks,
            )
        )

        metric_records = []

        memory_by_timestamp = {
            item["timestamp"]: item["value"]
            for item in memory_results
        }

        for cpu_item in cpu_results:
            timestamp = cpu_item["timestamp"]

            memory_value = memory_by_timestamp.get(
                timestamp,
            )

            if memory_value is None:
                continue

            metric_records.append(
                {
                    "timestamp": timestamp,
                    "cpu_usage_percent": cpu_item["value"],
                    "memory_usage_percent": memory_value,
                    "storage_usage_percent": storage_usage_percent,
                }
            )

        return metric_records

    def get_vm_guest_disks(
        self,
        vm,
    ) -> list[dict]:
        """
        Return raw guest disk information for a VM.
        """

        guest_info = getattr(vm, "guest", None)

        if guest_info is None:
            return []

        guest_disks = getattr(guest_info, "disk", None)

        if not guest_disks:
            return []

        disks = []

        for disk in guest_disks:
            disks.append(
                {
                    "disk_path": getattr(
                        disk,
                        "diskPath",
                        None,
                    ),
                    "capacity": getattr(
                        disk,
                        "capacity",
                        None,
                    ),
                    "free_space": getattr(
                        disk,
                        "freeSpace",
                        None,
                    ),
                    "filesystem_type": getattr(
                        disk,
                        "filesystemType",
                        None,
                    ),
                }
            )

        return disks