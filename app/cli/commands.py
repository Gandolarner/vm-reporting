import typer
from rich.console import Console

from app.cli.debug_commands import debug_app
from app.database.connection import init_db
from app.services.aggregation_service import run_monthly_aggregation
from app.services.collection_service import run_metric_collection
from app.services.reporting_service import create_monthly_report
from app.services.workflow_service import run_monthly_workflow, run_daily_workflow
from app.services.demo_data_service import seed_demo_data


cli_app = typer.Typer(
    help=(
        "VM reporting application for collecting, "
        "aggregating and reporting vCenter metrics."
    )
)

cli_app.add_typer(
    debug_app,
    name="debug",
)

console = Console()

@cli_app.command("init-db")
def init_database() -> None:
    """
    Initialize the database.
    """

    console.print(
        "[bold green]Initializing the database...[/bold green]"
    )

    init_db()

    console.print(
        "[bold green]Database initialized successfully.[/bold green]"
    )

@cli_app.command("collect-metrics")
def collect_metrics() -> None:
    """
    Collect VM metrics from vCenter.
    """

    console.print(
        "[green]Metric collection started.[/green]"
    )

    stored_record_count = run_metric_collection()

    console.print(
        f"[green]Stored "
        f"{stored_record_count} MetricRecords.[/green]"
    )

    console.print(
        "[green]Metric collection completed.[/green]"
    )

@cli_app.command("aggregate")
def aggregate(
    month: str,
) -> None:
    """
    Aggregate collected VM metrics
    for the given month.
    """

    console.print(
        f"[green]Aggregate command started "
        f"for month {month}.[/green]"
    )

    processed_vm_count = run_monthly_aggregation(
        month,
    )

    console.print(
        f"[green]Aggregated and evaluated "
        f"{processed_vm_count} VMs "
        f"for month {month}.[/green]"
    )

@cli_app.command("report")
def report(
    month: str,
) -> None:
    """
    Create a monthly VM utilization report.
    """

    console.print(
        f"[green]Report command started "
        f"for month {month}.[/green]"
    )

    report_path = create_monthly_report(
        month,
    )

    if report_path is None:
        console.print(
            f"[yellow]No aggregates found "
            f"for month {month}.[/yellow]"
        )
        return

    console.print(
        f"[green]Report created:[/green] "
        f"{report_path}"
    )

@cli_app.command("monthly-workflow")
def monthly_workflow() -> None:
    """
    Aggregate and report the previous month.
    """

    console.print(
        "[green]Monthly workflow started.[/green]"
    )

    (
        month,
        processed_vm_count,
        report_path,
    ) = run_monthly_workflow()

    if processed_vm_count == 0:
        console.print(
            f"[yellow]No metric records found "
            f"for month {month}. "
            f"Skipping report generation.[/yellow]"
        )
        return

    if report_path is None:
        console.print(
            f"[yellow]No report created "
            f"for month {month}.[/yellow]"
        )
        return

    console.print(
        f"[green]Aggregated and evaluated "
        f"{processed_vm_count} VMs "
        f"for month {month}.[/green]"
    )

    console.print(
        f"[green]Report created:[/green] "
        f"{report_path}"
    )

    console.print(
        f"[green]Monthly workflow completed "
        f"for {month}.[/green]"
    )

@cli_app.command("daily-workflow")
def daily_workflow() -> None:
    """
    Run the daily metric collection workflow.
    """

    console.print("[green]Daily workflow started.[/green]")

    stored_record_count = run_daily_workflow()

    console.print(f"[green]Stored {stored_record_count} MetricRecords.[/green]")

    console.print("[green]Daily workflow completed.[/green]")

@cli_app.command("seed-demo-data")
def seed_demo_data_command(
    month: str,
) -> None:
    """
    Insert demo data for local presentation without vCenter access.
    """

    console.print(
        f"[green]Seeding demo data for month {month}.[/green]"
    )

    created_records = seed_demo_data(
        month,
    )

    console.print(
        f"[green]Created {created_records} demo MetricRecords.[/green]"
    )