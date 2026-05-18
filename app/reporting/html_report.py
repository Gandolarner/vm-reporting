from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings
from app.database.models import (
    EvaluationResult,
    MonthlyAggregate,
    VirtualMachine,
)


STATUS_COLORS = {
    "CRITICAL": "#ff4d4d",
    "WARNING": "#ffcc00",
    "NORMAL": "#66cc66",
    "UNDERUTILIZED": "#66b3ff",
    "NO_DATA": "#cccccc",
}

STATUS_LABELS = {
    "CRITICAL": "Critical",
    "WARNING": "Warning",
    "NORMAL": "Normal",
    "UNDERUTILIZED": "Underutilized",
    "NO_DATA": "No data",
}

STATUS_PRIORITY = {
    "CRITICAL": 1,
    "WARNING": 2,
    "NORMAL": 3,
    "UNDERUTILIZED": 4,
    "NO_DATA": 5,
}


def get_status_color(
    status: str | None,
) -> str:
    if status is None:
        return "#cccccc"

    return STATUS_COLORS.get(
        status,
        "#cccccc",
    )


def get_status_priority(
    status: str | None,
) -> int:
    if status is None:
        return 99

    return STATUS_PRIORITY.get(
        status,
        99,
    )


def format_value(
    value: float | None,
) -> str:
    if value is None:
        return "-"

    return f"{value:.2f}"


def format_sort_value(
    value: float | int | str | None,
) -> str:
    if value is None:
        return ""

    return str(value)


def load_static_file(
    file_name: str,
) -> str:
    static_path = (
        Path(__file__).parent
        / "static"
        / file_name
    )

    return static_path.read_text(
        encoding="utf-8",
    )


def get_template_environment() -> Environment:
    template_path = (
        Path(__file__).parent
        / "templates"
    )

    return Environment(
        loader=FileSystemLoader(template_path),
        autoescape=True,
    )


def build_legend_items() -> list[dict]:
    return [
        {
            "status": status,
            "label": label,
            "color": get_status_color(status),
        }
        for status, label in STATUS_LABELS.items()
    ]


def build_inventory_cards(
    inventory_vm_count: int,
    vm_count_with_metrics: int,
    vms_without_metrics_count: int,
) -> list[dict]:
    return [
        {
            "title": "Inventory VMs",
            "value": inventory_vm_count,
        },
        {
            "title": "VMs with Metrics",
            "value": vm_count_with_metrics,
        },
        {
            "title": "VMs without Metrics",
            "value": vms_without_metrics_count,
        },
    ]


def build_status_cards(
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> list[dict]:
    status_counts = {
        status: 0
        for status in STATUS_LABELS
    }

    for _, _, evaluation in results:
        status = evaluation.overall_status or "NO_DATA"

        if status in status_counts:
            status_counts[status] += 1

    return [
        {
            "status": status,
            "title": STATUS_LABELS[status],
            "value": count,
            "color": get_status_color(status),
        }
        for status, count in status_counts.items()
    ]


def build_metric_cell(
    value: float | None,
    status: str | None,
) -> dict:
    return {
        "value": value,
        "value_display": format_value(value),
        "sort_value": format_sort_value(value),
        "status": status,
        "status_color": get_status_color(status),
    }


def build_main_rows(
    sorted_results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> list[dict]:
    rows = []

    for aggregate, vm, evaluation in sorted_results:
        overall_status = (
            evaluation.overall_status
            or "NO_DATA"
        )

        rows.append(
            {
                "vm_name": vm.name,
                "metric_record_count": (
                    aggregate.metric_record_count
                ),
                "metrics": [
                    build_metric_cell(
                        aggregate.cpu_avg_percent,
                        evaluation.cpu_status,
                    ),
                    build_metric_cell(
                        aggregate.memory_avg_percent,
                        evaluation.memory_status,
                    ),
                    build_metric_cell(
                        aggregate.storage_avg_percent,
                        evaluation.storage_status,
                    ),
                ],
                "overall_status": overall_status,
                "overall_color": get_status_color(
                    overall_status,
                ),
                "overall_sort_value": get_status_priority(
                    overall_status,
                ),
            }
        )

    return rows


def build_top_table(
    title: str,
    metric_name: str,
    status_name: str,
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> dict:
    sorted_results = sorted(
        results,
        key=lambda item: getattr(
            item[0],
            metric_name,
        )
        or 0,
        reverse=True,
    )[:5]

    rows = []

    for aggregate, vm, evaluation in sorted_results:
        value = getattr(
            aggregate,
            metric_name,
        )

        status = getattr(
            evaluation,
            status_name,
        )

        rows.append(
            {
                "vm_name": vm.name,
                "value_display": format_value(value),
                "status_color": get_status_color(status),
            }
        )

    return {
        "title": title,
        "rows": rows,
    }


def build_top_tables(
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> list[dict]:
    return [
        build_top_table(
            "Top CPU Usage",
            "cpu_avg_percent",
            "cpu_status",
            results,
        ),
        build_top_table(
            "Top Memory Usage",
            "memory_avg_percent",
            "memory_status",
            results,
        ),
        build_top_table(
            "Top Storage Usage",
            "storage_avg_percent",
            "storage_status",
            results,
        ),
    ]


def generate_html_report(
    month: str,
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
    inventory_vm_count: int,
    vms_without_metrics: list[VirtualMachine],
) -> Path:
    """
    Generate an HTML report for a month.
    """

    reports_dir = Path(settings.REPORT_OUTPUT_DIR)

    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = reports_dir / f"report_{month}.html"

    created_at = datetime.now(UTC).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    sorted_results = sorted(
        results,
        key=lambda item: get_status_priority(
            item[2].overall_status,
        ),
    )

    critical_or_warning_count = sum(
        1
        for _, _, evaluation in results
        if evaluation.overall_status
        in [
            "CRITICAL",
            "WARNING",
        ]
    )

    template_env = get_template_environment()

    template = template_env.get_template(
        "monthly_report.html.j2",
    )

    html = template.render(
        month=month,
        created_at=created_at,
        css=load_static_file("report.css"),
        javascript=load_static_file("report.js"),
        inventory_vm_count=inventory_vm_count,
        vm_count_with_metrics=len(results),
        vms_without_metrics_count=len(
            vms_without_metrics,
        ),
        critical_or_warning_count=critical_or_warning_count,
        legend_items=build_legend_items(),
        inventory_cards=build_inventory_cards(
            inventory_vm_count,
            len(results),
            len(vms_without_metrics),
        ),
        status_cards=build_status_cards(results),
        top_tables=build_top_tables(results),
        main_rows=build_main_rows(sorted_results),
        vms_without_metrics=vms_without_metrics,
    )

    report_path.write_text(
        html,
        encoding="utf-8",
    )

    return report_path