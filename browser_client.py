
from contextlib import contextmanager

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from config import CDP_URL, TARGET_URL

class BrowserClient:
    """Mengelola koneksi ke Chromium melalui Chrome DevTools Protocol."""

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def connect(self) -> Page:
        """Hubungkan ke Chromium yang sudah berjalan."""
        self.playwright = sync_playwright().start()

        try:
            self.browser = self.playwright.chromium.connect_over_cdp(
                CDP_URL
            )

            if not self.browser.contexts:
                raise RuntimeError(
                    "Tidak ditemukan browser context pada Chromium."
                )

            self.context = self.browser.contexts[0]

            for existing_page in self.context.pages:
                if "cloud.digitalocean.com" in existing_page.url:
                    self.page = existing_page
                    break

            if self.page is None:
                self.page = self.context.new_page()
                self.page.goto(
                    TARGET_URL,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

            return self.page

        except Exception:
            self.disconnect()
            raise

    def disconnect(self) -> None:
        """Lepaskan koneksi Playwright tanpa sengaja menutup Chromium."""
        if self.playwright is not None:
            self.playwright.stop()

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None


@contextmanager
def connect_browser():
    """Context manager agar koneksi selalu dibersihkan."""
    client = BrowserClient()

    try:
        page = client.connect()
        yield page
    finally:
        client.disconnect()