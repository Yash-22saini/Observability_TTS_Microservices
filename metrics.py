"""
metrics.py
----------
Prometheus counters for the /metrics endpoint.
These are used internally — the actual saved file is handled by logger.py.
"""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "tts_requests_total",
    "Total requests received",
    ["status"]
)

REQUEST_LATENCY = Histogram(
    "tts_latency_seconds",
    "Request latency in seconds",
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0]
)

ERROR_COUNT = Counter(
    "tts_errors_total",
    "Total failed requests"
)

AUDIO_SIZE = Histogram(
    "tts_audio_bytes",
    "Generated audio size in bytes",
    buckets=[5000, 10000, 30000, 60000, 100000]
)


def get_metrics_output():
    """Return Prometheus metrics for GET /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST