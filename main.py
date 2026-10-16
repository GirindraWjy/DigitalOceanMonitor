
from datetime import datetime

from browser_client import connect_browser
from metrics_collector import collect_metrics, latest_value
from dashboard import render_dashboard
from screenshot import capture_dashboard
from discord_sender import send_image
from config import (
    prepare_directories,
    validate_config,
)


METRIC_LABELS = {
    "cpu_usage": "CPU Usage",
    "cpu_load": "CPU Load Average",
    "memory": "Memory",
    "disk_usage": "Disk Usage",
    "disk_io": "Disk I/O",
    "bandwidth": "Bandwidth",
}


def format_value(value: float) -> str:
    """Format angka agar ringkas dan mudah dibaca."""
    return f"{value:,.2f}"


def format_metric_value(metric_name: str, value: float) -> str:
    """Format nilai metrik dengan satuan yang sesuai."""

    if metric_name in ("cpu_usage", "memory", "disk_usage"):
        return f"{value:.2f}%"

    if metric_name == "cpu_load":
        return f"{value:.2f}"

    if metric_name == "disk_io":
        # Asumsi nilai API dalam byte per detik.
        mb_per_sec = value / 1_000_000
        if mb_per_sec >= 1:
            return f"{mb_per_sec:.2f} MB/s"

        kb_per_sec = value / 1_000
        if kb_per_sec >= 1:
            return f"{kb_per_sec:.2f} KB/s"

        return f"{value:.2f} B/s"

    if metric_name == "bandwidth":
        # Asumsi nilai API dalam byte per detik.
        mbps = value * 8 / 1_000_000
        if mbps >= 1:
            return f"{mbps:.2f} Mbps"

        kbps = value * 8 / 1_000
        if kbps >= 1:
            return f"{kbps:.2f} Kbps"

        return f"{value * 8:.2f} bps"

    return f"{value:,.2f}"

def build_discord_message(result: dict) -> str:
    """Susun pesan Discord dari nilai terakhir setiap series."""

    lines = [
        "📊 DigitalOcean  Monitor",
        f"🕒 Collected: {result['collected_at']}",
        "",
        "📈 Latest Metrics",
    ]

    metrics = result["metrics"]

    for metric_name, payload in metrics.items():
        label = METRIC_LABELS.get(
            metric_name,
            metric_name.replace("_", " ").title(),
        )

        lines.append(f"\n**{label}**")

        for series in payload.get("series", []):
            series_name = series.get("name", "Unknown")
            latest = latest_value(payload, series_name)

            if latest is None:
                lines.append(f"• {series_name}: N/A")
                continue

            value = latest["value"]
            timestamp = latest["timestamp"]

            time_text = datetime.fromtimestamp(
                timestamp / 1000
            ).astimezone().strftime("%H:%M:%S")

            formatted_value = format_metric_value(metric_name, value)

            lines.append(
                f"• {series_name}: {formatted_value} "
                f"(data: {time_text})"
            )

    return "\n".join(lines)


def main() -> None:
    print("=== mulai monitor ===")

    validate_config()
    prepare_directories()

    print("[1/4] ngambil metrik DigitalOcean")

    with connect_browser() as page:
        result = collect_metrics(page)

    print("[2/4] Membuat dashboard HTML...")
    html_path = render_dashboard(result)
    print(f"HTML: {html_path}")

    print("[3/4] playwright ss")
    image_path = capture_dashboard()
    print(f"PNG: {image_path}")

    print("[4/4] kirim ke dc")
    message = build_discord_message(result)

    send_image(image_path, message)

    print("=== rampung ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERROR: {error}")
        raise