"""Latency instrumentation for application request workflows."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


@dataclass
class LatencyTimer:
    """Measure elapsed time for a request workflow."""

    started_at: float
    stages: dict[str, float]

    @classmethod
    def start(cls) -> "LatencyTimer":
        """Start a new latency timer."""
        return cls(
            started_at=perf_counter(),
            stages={},
        )

    def record(self, stage: str, started_at: float) -> float:
        """Record elapsed milliseconds for a stage."""
        elapsed_ms = (perf_counter() - started_at) * 1000
        self.stages[stage] = round(elapsed_ms, 2)
        return elapsed_ms

    def total_ms(self) -> float:
        """Return total elapsed milliseconds."""
        return round(
            (perf_counter() - self.started_at) * 1000,
            2,
        )
