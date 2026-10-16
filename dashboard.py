
import json
from datetime import datetime, timezone
from pathlib import Path

from config import (
    DASHBOARD_HTML,
    DASHBOARD_TEMPLATE,
    prepare_directories,
)

WINDOW_MS = 60 * 60 * 1000


def build_dashboard_data(result: dict) -> dict:
    """Siapkan seluruh series dalam jendela satu jam."""

    metrics = result["metrics"]

    # Cari timestamp paling baru yang benar-benar memiliki nilai numerik.
    timestamps = []

    for payload in metrics.values():
        for series in payload.get("series", []):
            for point in series.get("values", []):
                if (
                    isinstance(point, (list, tuple))
                    and len(point) >= 2
                    and isinstance(point[0], (int, float))
                    and isinstance(point[1], (int, float))
                ):
                    timestamps.append(point[0])

    if not timestamps:
        raise ValueError("Tidak ditemukan titik data numerik.")

    end_ms = max(timestamps)
    start_ms = end_ms - WINDOW_MS

    charts = {}

    for metric_name, payload in metrics.items():
        series_list = []

        for series in payload.get("series", []):
            points = []

            for point in series.get("values", []):
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    continue

                timestamp, value = point[0], point[1]

                if not isinstance(timestamp, (int, float)):
                    continue

                if not isinstance(value, (int, float)):
                    continue

                if start_ms <= timestamp <= end_ms:
                    points.append({
                        "timestamp": timestamp,
                        "value": value,
                    })

            points.sort(key=lambda item: item["timestamp"])

            series_list.append({
                "name": series.get("name", "Unknown"),
                "points": points,
            })

        charts[metric_name] = series_list

    return {
        "droplet_id": result["droplet_id"],
        "collected_at": result["collected_at"],
        "window_start": start_ms,
        "window_end": end_ms,
        "window_minutes": 60,
        "charts": charts,
    }


def render_dashboard(result: dict) -> Path:
    """Generate HTML dashboard dengan data historis satu jam."""

    prepare_directories()

    if not DASHBOARD_TEMPLATE.exists():
        raise FileNotFoundError(
            f"Template tidak ditemukan: {DASHBOARD_TEMPLATE}"
        )

    data = build_dashboard_data(result)
    template = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")

    data_json = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
    )

    html = template.replace("__DASHBOARD_DATA__", data_json)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")

    return DASHBOARD_HTML