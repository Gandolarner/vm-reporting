import logging
from pathlib import Path


def configure_logging() -> None:
    """
    Configure application logging.
    """

    log_dir = Path("logs")
    log_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_dir / "vm_reporting.log"

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            ),
        ],
    )