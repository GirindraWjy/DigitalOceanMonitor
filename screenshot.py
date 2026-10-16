
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import DASHBOARD_HTML, DASHBOARD_PNG, prepare_directories


def capture_dashboard() -> Path:
    """Render dashboard HTML menjadi screenshot PNG."""

    prepare_directories()

    if not DASHBOARD_HTML.exists():
        raise FileNotFoundError(
            f"Dashboard HTML tidak ditemukan: {DASHBOARD_HTML}"
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page(
                viewport={"width": 1440, "height": 1100},
                device_scale_factor=1,
            )

            page.goto(
                DASHBOARD_HTML.resolve().as_uri(),
                wait_until="networkidle",
                timeout=30_000,
            )

            page.screenshot(
                path=str(DASHBOARD_PNG),
                full_page=True,
                animations="disabled",
            )

        finally:
            browser.close()

    return DASHBOARD_PNG