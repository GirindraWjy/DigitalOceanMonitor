
import time
from datetime import datetime, timezone
from typing import Any

from playwright.sync_api import Page, Response

from config import METRIC_NAMES, TARGET_URL


API_PREFIX = (
    "/api/v1/insights/graphs/data/droplet_metrics/"
)

COLLECTION_TIMEOUT_MS = 15_000


def collect_metrics(page: Page) -> dict[str, Any]:
    """Tangkap data metrik dari respons API halaman DigitalOcean."""

    metrics: dict[str, Any] = {}
    errors: list[str] = []

    def handle_response(response: Response) -> None:
        url = response.url

        if API_PREFIX not in url:
            return

        metric_name = url.split(API_PREFIX, 1)[1].split("?", 1)[0]
        metric_name = metric_name.rstrip("/")

        if metric_name not in METRIC_NAMES:
            return

        if not response.ok:
            errors.append(
                f"{metric_name}: HTTP {response.status}"
            )
            return

        try:
            payload = response.json()

            if isinstance(payload, dict) and "series" in payload:
                metrics[metric_name] = payload

        except Exception as error:
            errors.append(
                f"{metric_name}: gagal membaca JSON ({error})"
            )

    # Listener harus dipasang sebelum halaman dimuat ulang.
    page.on("response", handle_response)

    try:
        page.goto(
            TARGET_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        # Beri waktu agar grafik memuat data dari API.
        deadline = time.monotonic() + (
            COLLECTION_TIMEOUT_MS / 1000
        )

        while time.monotonic() < deadline:
            if all(name in metrics for name in METRIC_NAMES):
                break

            page.wait_for_timeout(250)

    finally:
        page.remove_listener("response", handle_response)

    missing = [
        name for name in METRIC_NAMES
        if name not in metrics
    ]

    if missing:
        details = "; ".join(errors) if errors else "Tidak ada respons yang cocok."
        raise RuntimeError(
            f"Metrik belum lengkap: {', '.join(missing)}. "
            f"Detail: {details} "
            "Pastikan halaman Insights selesai dimuat dan grafik tersedia."
        )

    return {
        "droplet_id": "578500091",
        "url": TARGET_URL,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }




def latest_value(
    metric_payload: dict,
    series_name: str,
) -> dict | None:
    """Ambil titik data numerik terakhir yang valid."""

    for series in metric_payload.get("series", []):
        if series.get("name") != series_name:
            continue

        values = series.get("values", [])

        for point in reversed(values):
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            timestamp, value = point[0], point[1]

            if (
                isinstance(timestamp, (int, float))
                and isinstance(value, (int, float))
            ):
                return {
                    "timestamp": timestamp,
                    "value": float(value),
                }

        return None

    return None