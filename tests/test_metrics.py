"""Tests for legalops.metrics — Prometheus exposition."""

from __future__ import annotations

import threading

import pytest

from legalops.metrics import DEFAULT_BUCKETS, MetricsRegistry


def test_counter_increments() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.counter("foo_total", 2)
    r.counter("foo_total", 3)

    # Assert
    out = r.render()
    assert "foo_total 5" in out
    assert "# TYPE foo_total counter" in out


def test_counter_negative_rejected() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act / Assert
    with pytest.raises(ValueError):
        r.counter("bad", -1)


def test_gauge_set_overrides() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.gauge("temp", 10.0)
    r.gauge("temp", 42.0)

    # Assert
    out = r.render()
    assert "temp 42" in out
    assert "# TYPE temp gauge" in out


def test_histogram_buckets_default() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.histogram("lat_seconds", 0.05)
    r.histogram("lat_seconds", 0.5)
    out = r.render()

    # Assert
    for upper in DEFAULT_BUCKETS:
        assert f'le="{float(upper)}"' in out or f'le="{upper}"' in out
    assert 'le="+Inf"' in out
    assert "lat_seconds_count" in out
    assert "lat_seconds_sum" in out


def test_histogram_custom_buckets() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.histogram("custom", 2.5, buckets=[1.0, 5.0])

    # Assert
    out = r.render()
    assert 'custom_bucket{le="1.0"} 0' in out
    assert 'custom_bucket{le="5.0"} 1' in out
    assert 'custom_bucket{le="+Inf"} 1' in out
    assert "custom_count 1" in out


def test_render_exposition_format_headers() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.counter("a_total", 1, help_text="some help")
    out = r.render()

    # Assert
    assert "# HELP a_total some help" in out
    assert "# TYPE a_total counter" in out
    assert out.endswith("\n")


def test_labels_rendering_sorted() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.counter("req_total", 1, labels={"path": "/x", "method": "GET"})
    r.counter("req_total", 1, labels={"path": "/x", "method": "GET"})
    out = r.render()

    # Assert
    assert 'req_total{method="GET",path="/x"} 2' in out


def test_labels_distinct_series() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    r.counter("c", 1, labels={"k": "a"})
    r.counter("c", 4, labels={"k": "b"})
    out = r.render()

    # Assert
    assert 'c{k="a"} 1' in out
    assert 'c{k="b"} 4' in out


def test_metric_kind_conflict() -> None:
    # Arrange
    r = MetricsRegistry()
    r.counter("x", 1)

    # Act / Assert
    with pytest.raises(ValueError):
        r.gauge("x", 1.0)


def test_thread_safety_counter_smoke() -> None:
    # Arrange
    r = MetricsRegistry()
    iters = 500
    threads = [
        threading.Thread(target=lambda: [r.counter("hits", 1) for _ in range(iters)])
        for _ in range(4)
    ]

    # Act
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Assert
    out = r.render()
    assert f"hits {iters * 4}" in out


def test_render_empty_registry() -> None:
    # Arrange
    r = MetricsRegistry()

    # Act
    out = r.render()

    # Assert
    assert out == "\n"
