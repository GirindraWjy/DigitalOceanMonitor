
from pathlib import Path

import requests

from config import DC_WEBHOOK


def send_image(image_path: Path, content: str = "") -> None:
    """Kirim screenshot PNG ke Discord webhook."""

    if not DC_WEBHOOK:
        raise ValueError("DC_WEBHOOK belum diisi di file .env.")

    if not image_path.exists():
        raise FileNotFoundError(
            f"File screenshot tidak ditemukan: {image_path}"
        )

    with image_path.open("rb") as image_file:
        response = requests.post(
            DC_WEBHOOK,
            data={"content": content},
            files={
                "file": (
                    image_path.name,
                    image_file,
                    "image/png",
                )
            },
            timeout=30,
        )

    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Gagal mengirim screenshot ke Discord: "
            f"HTTP {response.status_code} - {response.text}"
        )

    print("Screenshot berhasil dikirim ke Discord.")