import typer
from rich.console import Console
from rich.table import Table

from app.database.connection import SessionLocal
from app.database.models import EvaluationResult, MonthlyAggregate, VirtualMachine


debug_app = typer.Typer(
    help="Debug and inspection commands."
)

console = Console()

@debug_app.command("show-aggregates")
def show_aggregates(
    month: str,
    limit: int = 20,
) -> None:
    """
    Show monthly aggregates and evaluations.
    """

    db = SessionLocal()

    try:
        results = (
            db.query(
                MonthlyAggregate,
                VirtualMachine,
                EvaluationResult,
            )
            .join(
                VirtualMachine,
                MonthlyAggregate.vm_id == VirtualMachine.id,
            )
            .join(
                EvaluationResult,
                EvaluationResult.monthly_aggregate_id == MonthlyAggregate.id,
            )
            .filter(
                MonthlyAggregate.month == month,
            )
            .limit(limit)
            .all()
        )

        table = Table(
            title=f"Monthly aggregates for {month}"
        )

        table.add_column("VM")
        table.add_column("Records", justify="right")
        table.add_column("CPU Avg", justify="right")
        table.add_column("Memory Avg", justify="right")
        table.add_column("Storage Avg", justify="right")
        table.add_column("Overall")
        table.add_column("Storage Status")

        for aggregate, vm, evaluation in results:
            table.add_row(
                vm.name,
                str(aggregate.metric_record_count),
                f"{aggregate.cpu_avg_percent:.2f}",
                f"{aggregate.memory_avg_percent:.2f}",
                (
                    f"{aggregate.storage_avg_percent:.2f}"
                    if aggregate.storage_avg_percent is not None
                    else "-"
                ),
                evaluation.overall_status,
                evaluation.storage_status or "-",
            )

        console.print(table)

    finally:
        db.close()

@debug_app.command("show-evaluations")
def show_evaluations(
    month: str,
    status: str | None = None,
    limit: int = 20,
) -> None:
    """
    Show evaluation results for a month.
    """

    db = SessionLocal()

    try:
        query = (
            db.query(
                EvaluationResult,
                MonthlyAggregate,
                VirtualMachine,
            )
            .join(
                MonthlyAggregate,
                EvaluationResult.monthly_aggregate_id
                == MonthlyAggregate.id,
            )
            .join(
                VirtualMachine,
                MonthlyAggregate.vm_id == VirtualMachine.id,
            )
            .filter(
                MonthlyAggregate.month == month,
            )
        )

        if status is not None:
            query = query.filter(
                EvaluationResult.overall_status == status.upper()
            )

        results = query.limit(limit).all()

        table = Table(
            title=f"Evaluation results for {month}"
        )

        table.add_column("VM")
        table.add_column("Overall")
        table.add_column("CPU")
        table.add_column("Memory")
        table.add_column("Storage")

        for evaluation, aggregate, vm in results:
            table.add_row(
                vm.name,
                evaluation.overall_status,
                evaluation.cpu_status,
                evaluation.memory_status,
                evaluation.storage_status or "-",
            )

        console.print(table)

    finally:
        db.close()