from datetime import UTC, datetime
from pathlib import Path
from app.config.settings import settings

from app.database.models import EvaluationResult, MonthlyAggregate, VirtualMachine


STATUS_COLORS = {
    "CRITICAL": "#ff4d4d",
    "WARNING": "#ffcc00",
    "NORMAL": "#66cc66",
    "UNDERUTILIZED": "#66b3ff",
}

STATUS_LABELS = {
    "CRITICAL": "Critical",
    "WARNING": "Warning",
    "NORMAL": "Normal",
    "UNDERUTILIZED": "Underutilized",
}

STATUS_PRIORITY = {
    "CRITICAL": 1,
    "WARNING": 2,
    "NORMAL": 3,
    "UNDERUTILIZED": 4,
}

def get_status_color(status: str | None) -> str:
    if status is None:
        return "#cccccc"

    return STATUS_COLORS.get(status, "#cccccc")

def get_status_priority(status: str | None) -> int:
    if status is None:
        return 99

    return STATUS_PRIORITY.get(status, 99)

def format_value_with_status(
    value: float | None,
    status: str | None,
) -> str:
    if value is None:
        formatted_value = "-"
    else:
        formatted_value = f"{value:.2f}"

    color = get_status_color(status)

    return f"""
    <span class="metric-value">
        <span
            class="status-dot"
            style="background-color: {color};"
        ></span>
        {formatted_value}
    </span>
    """

def format_status_badge(status: str | None) -> str:
    label = status or "UNKNOWN"
    color = get_status_color(status)

    return f"""
    <span
        class="status-badge"
        style="background-color: {color};"
    >
        {label}
    </span>
    """

def generate_legend() -> str:
    legend_items = []

    for status, label in STATUS_LABELS.items():
        color = get_status_color(status)

        legend_items.append(
            f"""
            <div class="legend-item">
                <span
                    class="status-dot"
                    style="background-color: {color};"
                ></span>
                <span>{label}</span>
            </div>
            """
        )

    return f"""
    <section class="legend">
        <h2>Status legend</h2>
        <div class="legend-items">
            {"".join(legend_items)}
        </div>
    </section>
    """

def format_sort_value(
    value: float | int | str | None,
) -> str:
    if value is None:
        return ""

    return str(value)

def generate_table_rows(
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> str:
    rows = []

    for aggregate, vm, evaluation in results:
        storage_value = aggregate.storage_avg_percent

        rows.append(
            f"""
            <tr>
                <td data-sort-value="{vm.name}">
                    {vm.name}
                </td>

                <td data-sort-value="{aggregate.metric_record_count}">
                    {aggregate.metric_record_count}
                </td>

                <td data-sort-value="{aggregate.cpu_avg_percent}">
                    {format_value_with_status(
                        aggregate.cpu_avg_percent,
                        evaluation.cpu_status,
                    )}
                </td>

                <td data-sort-value="{aggregate.memory_avg_percent}">
                    {format_value_with_status(
                        aggregate.memory_avg_percent,
                        evaluation.memory_status,
                    )}
                </td>

                <td data-sort-value="{format_sort_value(storage_value)}">
                    {format_value_with_status(
                        storage_value,
                        evaluation.storage_status,
                    )}
                </td>

                <td data-sort-value="{get_status_priority(evaluation.overall_status)}">
                    {format_status_badge(
                        evaluation.overall_status,
                    )}
                </td>
            </tr>
            """
        )

    return "".join(rows)

def generate_top_table(
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
) -> str:
    sorted_results = sorted(
        results,
        key=lambda item: getattr(
            item[0],
            metric_name,
        ) or 0,
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
            f"""
            <tr>
                <td>{vm.name}</td>
                <td>
                    {format_value_with_status(
                        value,
                        status,
                    )}
                </td>
            </tr>
            """
        )

    return f"""
    <div class="top-table-card">
        <h3>{title}</h3>

        <table>
            <thead>
                <tr>
                    <th>VM</th>
                    <th>Value</th>
                </tr>
            </thead>

            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </div>
    """

def generate_summary_cards(
    results: list[
        tuple[
            MonthlyAggregate,
            VirtualMachine,
            EvaluationResult,
        ]
    ],
) -> str:
    status_counts = {
        "CRITICAL": 0,
        "WARNING": 0,
        "NORMAL": 0,
        "UNDERUTILIZED": 0,
    }

    for _, _, evaluation in results:
        status = evaluation.overall_status

        if status in status_counts:
            status_counts[status] += 1

    cards = []

    for status, count in status_counts.items():
        cards.append(
            f"""
            <div
                class="summary-card"
                style="background-color: {get_status_color(status)};"
            >
                <div class="summary-card-title">
                    {STATUS_LABELS[status]}
                </div>

                <div class="summary-card-value">
                    {count}
                </div>
            </div>
            """
        )

    return f"""
    <section class="summary-section">
        {"".join(cards)}
    </section>
    """

def generate_inventory_summary_cards(
    inventory_vm_count: int,
    vm_count_with_metrics: int,
    vms_without_metrics_count: int,
) -> str:
    return f"""
    <section class="summary-section">
        <div class="summary-card">
            <div class="summary-card-title">
                Inventory VMs
            </div>
            <div class="summary-card-value">
                {inventory_vm_count}
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-card-title">
                VMs with Metrics
            </div>
            <div class="summary-card-value">
                {vm_count_with_metrics}
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-card-title">
                VMs without Metrics
            </div>
            <div class="summary-card-value">
                {vms_without_metrics_count}
            </div>
        </div>
    </section>
    """


def generate_vms_without_metrics_table(
    vms_without_metrics: list[VirtualMachine],
) -> str:
    if not vms_without_metrics:
        return ""

    rows = []

    for vm in vms_without_metrics:
        rows.append(
            f"""
            <tr>
                <td>{vm.name}</td>
            </tr>
            """
        )

    return f"""
    <section class="section">
        <h2>VMs without Metric Records</h2>

        <table>
            <thead>
                <tr>
                    <th>VM</th>
                </tr>
            </thead>

            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </section>
    """

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
    reports_dir.mkdir(parents=True, exist_ok=True)

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
        if evaluation.overall_status in [
            "CRITICAL",
            "WARNING",
        ]
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>VM Report {month}</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #222222;
            }}

            h1 {{
                margin-bottom: 10px;
            }}

            h2 {{
                margin-top: 0;
                font-size: 18px;
            }}

            h3 {{
                margin-top: 0;
            }}

            .report-meta {{
                margin-bottom: 24px;
            }}

            .section {{
                margin-bottom: 32px;
            }}

            .legend {{
                border: 1px solid #dddddd;
                background: #fafafa;
                padding: 16px;
                margin-bottom: 24px;
                border-radius: 6px;
            }}

            .legend-items {{
                display: flex;
                flex-wrap: wrap;
                gap: 18px;
            }}

            .legend-item {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 14px;
            }}

            .summary-section {{
                display: flex;
                gap: 16px;
                margin-bottom: 32px;
                flex-wrap: wrap;
            }}

            .summary-card {{
                min-width: 180px;
                padding: 18px;
                border-radius: 8px;
                border: 1px solid #666666;
            }}

            .summary-card-title {{
                font-size: 14px;
                margin-bottom: 8px;
            }}

            .summary-card-value {{
                font-size: 32px;
                font-weight: bold;
            }}

            .top-tables {{
                display: flex;
                gap: 20px;
                margin-bottom: 32px;
                flex-wrap: wrap;
            }}

            .top-table-card {{
                flex: 1;
                min-width: 280px;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
            }}

            th, td {{
                border: 1px solid #cccccc;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: #eeeeee;
                cursor: pointer;
                user-select: none;
                white-space: nowrap;
            }}

            th:hover {{
                background-color: #dddddd;
            }}

            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}

            .metric-value {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}

            .status-dot {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                border: 1px solid #666666;
            }}

            .status-badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                color: #111111;
                border: 1px solid #666666;
            }}

            .sort-hint {{
                font-size: 12px;
                color: #666666;
                margin-bottom: 8px;
            }}

            .sort-indicator {{
                display: inline-block;
                width: 12px;
                margin-left: 4px;
                font-size: 10px;
            }}
        </style>

        <script>
            let sortDirections = {{}};

            function parseSortValue(value) {{
                if (value === null || value === undefined || value === "") {{
                    return null;
                }}

                const numberValue = Number(value);

                if (!Number.isNaN(numberValue)) {{
                    return numberValue;
                }}

                return value.toLowerCase();
            }}

            function updateSortIndicators(
                activeColumnIndex,
                direction,
            ) {{
                const table = document.getElementById(
                    "vm-report-table"
                );

                const headers = table.tHead.rows[0].cells;

                for (let i = 0; i < headers.length; i++) {{
                    const indicator = headers[i].querySelector(
                        ".sort-indicator"
                    );

                    if (indicator === null) {{
                        continue;
                    }}

                    if (i === activeColumnIndex) {{
                        indicator.textContent =
                            direction === "asc"
                                ? "▲"
                                : "▼";
                    }} else {{
                        indicator.textContent = "";
                    }}
                }}
            }}

            function sortTable(columnIndex) {{
                const table = document.getElementById(
                    "vm-report-table"
                );

                const tbody = table.tBodies[0];

                const rows = Array.from(tbody.rows);

                const currentDirection =
                    sortDirections[columnIndex] || "asc";

                const nextDirection =
                    currentDirection === "asc"
                        ? "desc"
                        : "asc";

                sortDirections = {{}};

                sortDirections[columnIndex] = nextDirection;

                rows.sort((rowA, rowB) => {{
                    const cellA = rowA.cells[columnIndex];
                    const cellB = rowB.cells[columnIndex];

                    const valueA = parseSortValue(
                        cellA.getAttribute(
                            "data-sort-value"
                        )
                    );

                    const valueB = parseSortValue(
                        cellB.getAttribute(
                            "data-sort-value"
                        )
                    );

                    if (
                        valueA === null
                        && valueB === null
                    ) {{
                        return 0;
                    }}

                    if (valueA === null) {{
                        return 1;
                    }}

                    if (valueB === null) {{
                        return -1;
                    }}

                    if (valueA < valueB) {{
                        return nextDirection === "asc"
                            ? -1
                            : 1;
                    }}

                    if (valueA > valueB) {{
                        return nextDirection === "asc"
                            ? 1
                            : -1;
                    }}

                    return 0;
                }});

                rows.forEach((row) =>
                    tbody.appendChild(row)
                );

                updateSortIndicators(
                    columnIndex,
                    nextDirection,
                );
            }}
        </script>
    </head>

    <body>
        <h1>VM Utilization Report</h1>

        <p class="report-meta">
            <strong>Month:</strong> {month}<br>
            <strong>Created at:</strong> {created_at}<br>
            <strong>Inventory VMs:</strong> {inventory_vm_count}<br>
            <strong>VMs with metrics:</strong> {len(results)}<br>
            <strong>VMs without metrics:</strong> {len(vms_without_metrics)}<br>
            <strong>Critical/Warning VMs:</strong> {critical_or_warning_count}
        </p>

        {generate_legend()}

        {generate_summary_cards(results)}

        {generate_inventory_summary_cards(
            inventory_vm_count,
            len(results),
            len(vms_without_metrics),
        )}

        <section class="section">
            <h2>Top Resource Consumers</h2>

            <div class="top-tables">
                {generate_top_table(
                    "Top CPU Usage",
                    "cpu_avg_percent",
                    "cpu_status",
                    results,
                )}

                {generate_top_table(
                    "Top Memory Usage",
                    "memory_avg_percent",
                    "memory_status",
                    results,
                )}

                {generate_top_table(
                    "Top Storage Usage",
                    "storage_avg_percent",
                    "storage_status",
                    results,
                )}
            </div>
        </section>

        <section class="section">
            <h2>All VMs</h2>

            <p class="sort-hint">
                Click a column header to sort the table.
            </p>

            <table id="vm-report-table">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">
                            VM
                            <span class="sort-indicator"></span>
                        </th>

                        <th onclick="sortTable(1)">
                            Records
                            <span class="sort-indicator"></span>
                        </th>

                        <th onclick="sortTable(2)">
                            CPU Avg %
                            <span class="sort-indicator"></span>
                        </th>

                        <th onclick="sortTable(3)">
                            Memory Avg %
                            <span class="sort-indicator"></span>
                        </th>

                        <th onclick="sortTable(4)">
                            Storage Avg %
                            <span class="sort-indicator"></span>
                        </th>

                        <th onclick="sortTable(5)">
                            Overall Status
                            <span class="sort-indicator">▲</span>
                        </th>
                    </tr>
                </thead>

                <tbody>
                    {generate_table_rows(sorted_results)}
                </tbody>
            </table>
        </section>

    {generate_vms_without_metrics_table(vms_without_metrics)}

    </body>
    </html>
    """

    report_path.write_text(
        html,
        encoding="utf-8",
    )

    return report_path