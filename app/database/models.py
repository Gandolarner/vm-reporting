from datetime import UTC, datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    moid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    metric_records: Mapped[list["MetricRecord"]] = relationship(back_populates="virtual_machine")
    monthly_aggregates: Mapped[list["MonthlyAggregate"]] = relationship(back_populates="virtual_machine")

class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    processed_vm_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_metric_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    metric_records: Mapped[list["MetricRecord"]] = relationship(back_populates="collection_run")

class MetricRecord(Base):
    __tablename__ = "metric_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vm_id: Mapped[int] = mapped_column(Integer, ForeignKey("virtual_machines.id"), nullable=False)
    collection_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("collection_runs.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_usage_percent: Mapped[float] = mapped_column(Float, nullable=True)
    storage_usage_percent: Mapped[float] = mapped_column(Float, nullable=True)
    power_state: Mapped[str] = mapped_column(String(20), nullable=False)

    virtual_machine: Mapped["VirtualMachine"] = relationship(back_populates="metric_records")
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="metric_records")

class MonthlyAggregate(Base):
    __tablename__ = "monthly_aggregates"
    __table_args__ = (UniqueConstraint("vm_id", "month", name="uq_monthly_aggregate_vm_month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vm_id: Mapped[int] = mapped_column(Integer, ForeignKey("virtual_machines.id"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    metric_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cpu_avg_percent: Mapped[float] = mapped_column(Float, nullable=True)
    cpu_min_percent: Mapped[float] = mapped_column(Float, nullable=True)
    cpu_max_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_avg_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_min_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_max_percent: Mapped[float] = mapped_column(Float, nullable=True)
    storage_avg_percent: Mapped[float] = mapped_column(Float, nullable=True)
    storage_min_percent: Mapped[float] = mapped_column(Float, nullable=True)
    storage_max_percent: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    virtual_machine: Mapped["VirtualMachine"] = relationship()
    evaluation_result: Mapped["EvaluationResult"] = relationship("EvaluationResult", back_populates="monthly_aggregate")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (UniqueConstraint("monthly_aggregate_id", name="uq_evaluation_result_monthly_aggregate",),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monthly_aggregate_id: Mapped[int] = mapped_column(Integer, ForeignKey("monthly_aggregates.id"), nullable=False)
    overall_status: Mapped[str] = mapped_column(String(20), nullable=False)
    cpu_status: Mapped[str] = mapped_column(String(20), nullable=True)
    memory_status: Mapped[str] = mapped_column(String(20), nullable=True)
    storage_status: Mapped[str] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    monthly_aggregate: Mapped["MonthlyAggregate"] = relationship(back_populates="evaluation_result")
