"""Prometheus text exposition format metrics registry.

In-memory only, thread-safe. Stdlib only.

Uso:
    >>> from legalops.metrics import MetricsRegistry
    >>> r = MetricsRegistry()
    >>> r.counter("emails_processed_total", 1, labels={"tribunal": "tjpr"})
    >>> print(r.render())
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Literal

MetricType = Literal["counter", "gauge", "histogram"]

DEFAULT_BUCKETS: tuple[float, ...] = (0.001, 0.01, 0.1, 1.0, 10.0)


@dataclass
class _Series:
    name: str
    kind: MetricType
    help_text: str
    # key = sorted-labels tuple
    counter_values: dict[tuple[tuple[str, str], ...], float] = field(default_factory=dict)
    gauge_values: dict[tuple[tuple[str, str], ...], float] = field(default_factory=dict)
    hist_buckets: tuple[float, ...] = DEFAULT_BUCKETS
    hist_counts: dict[tuple[tuple[str, str], ...], list[int]] = field(default_factory=dict)
    hist_sum: dict[tuple[tuple[str, str], ...], float] = field(default_factory=dict)
    hist_total: dict[tuple[tuple[str, str], ...], int] = field(default_factory=dict)


def _label_key(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted(labels.items()))


def _fmt_labels(key: tuple[tuple[str, str], ...], extra: tuple[str, str] | None = None) -> str:
    parts = [f'{k}="{_escape(v)}"' for k, v in key]
    if extra is not None:
        parts.append(f'{extra[0]}="{_escape(extra[1])}"')
    if not parts:
        return ""
    return "{" + ",".join(parts) + "}"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class MetricsRegistry:
    """Thread-safe in-memory metrics registry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._series: dict[str, _Series] = {}

    def _ensure(
        self,
        name: str,
        kind: MetricType,
        help_text: str,
        buckets: tuple[float, ...] | None = None,
    ) -> _Series:
        s = self._series.get(name)
        if s is None:
            s = _Series(
                name=name,
                kind=kind,
                help_text=help_text,
                hist_buckets=buckets if buckets is not None else DEFAULT_BUCKETS,
            )
            self._series[name] = s
        elif s.kind != kind:
            raise ValueError(f"metric {name!r} re-registered with different kind {kind}")
        return s

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
        help_text: str = "",
    ) -> None:
        if value < 0:
            raise ValueError("counter cannot decrease")
        with self._lock:
            s = self._ensure(name, "counter", help_text or f"counter {name}")
            k = _label_key(labels)
            s.counter_values[k] = s.counter_values.get(k, 0.0) + value

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        help_text: str = "",
    ) -> None:
        with self._lock:
            s = self._ensure(name, "gauge", help_text or f"gauge {name}")
            k = _label_key(labels)
            s.gauge_values[k] = value

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        buckets: list[float] | None = None,
        help_text: str = "",
    ) -> None:
        with self._lock:
            bkts = tuple(buckets) if buckets is not None else DEFAULT_BUCKETS
            s = self._ensure(name, "histogram", help_text or f"histogram {name}", bkts)
            k = _label_key(labels)
            if k not in s.hist_counts:
                s.hist_counts[k] = [0] * len(s.hist_buckets)
                s.hist_sum[k] = 0.0
                s.hist_total[k] = 0
            for i, upper in enumerate(s.hist_buckets):
                if value <= upper:
                    s.hist_counts[k][i] += 1
            s.hist_sum[k] += value
            s.hist_total[k] += 1

    def render(self) -> str:
        """Render Prometheus exposition format."""
        lines: list[str] = []
        with self._lock:
            for name in sorted(self._series):
                s = self._series[name]
                lines.append(f"# HELP {name} {s.help_text}")
                lines.append(f"# TYPE {name} {s.kind}")
                if s.kind == "counter":
                    for k, v in sorted(s.counter_values.items()):
                        lines.append(f"{name}{_fmt_labels(k)} {_fmt_num(v)}")
                elif s.kind == "gauge":
                    for k, v in sorted(s.gauge_values.items()):
                        lines.append(f"{name}{_fmt_labels(k)} {_fmt_num(v)}")
                else:  # histogram
                    for k in sorted(s.hist_counts):
                        for i, upper in enumerate(s.hist_buckets):
                            lines.append(
                                f"{name}_bucket{_fmt_labels(k, ('le', _num_label(upper)))} "
                                f"{s.hist_counts[k][i]}"
                            )
                        lines.append(
                            f"{name}_bucket{_fmt_labels(k, ('le', '+Inf'))} {s.hist_total[k]}"
                        )
                        lines.append(f"{name}_sum{_fmt_labels(k)} {_fmt_num(s.hist_sum[k])}")
                        lines.append(f"{name}_count{_fmt_labels(k)} {s.hist_total[k]}")
        return "\n".join(lines) + "\n"


def _fmt_num(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return repr(value)


def _num_label(value: float) -> str:
    if value == int(value):
        return f"{int(value)}.0"
    return repr(value)
