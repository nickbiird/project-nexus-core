"""
Command-line interface (CLI) for the Lead Generation Pipeline.
"""

import logging
import time
from pathlib import Path

import typer  # type: ignore


def configure_logging(level: int = logging.INFO) -> None:
    """Configure package-level logging with consistent format."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    pkg_logger = logging.getLogger("scripts.leadgen")
    pkg_logger.handlers.clear()
    pkg_logger.addHandler(handler)
    pkg_logger.setLevel(level)


log = logging.getLogger(__name__)

app = typer.Typer(help="Yellowbird Telemetry — Lead Generation Pipeline")


@app.command()
def from_apollo(input: Path, output: Path, dry_run: bool = False) -> None:
    """Process Apollo.io CSV export into verified CRM leads."""
    configure_logging()

    start_time = time.time()
    log.info("Starting from_apollo pipeline")

    # TODO: wire io.from_apollo_csv → verify.HunterClient →
    #       scoring.assign_tier → io.write_leads_csv

    elapsed = time.time() - start_time
    log.info("Finished from_apollo pipeline in %.2fs", elapsed)


@app.command()
def from_sabi(input: Path, output: Path, dry_run: bool = False) -> None:
    """Process SABI XLSX export into scored CRM leads."""
    configure_logging()

    start_time = time.time()
    log.info("Starting from_sabi pipeline")

    # TODO: wire io.from_sabi_xlsx → scoring.assign_tier →
    #       io.write_leads_csv (no Hunter needed — SABI has verified emails)

    elapsed = time.time() - start_time
    log.info("Finished from_sabi pipeline in %.2fs", elapsed)


@app.command()
def score(input: Path) -> None:
    """Re-score an existing yellowbird_leads.csv and print tier assignments."""
    configure_logging()

    start_time = time.time()
    log.info("Starting score pipeline")

    # TODO: read existing CSV → Lead objects → scoring → print table

    elapsed = time.time() - start_time
    log.info("Finished score pipeline in %.2fs", elapsed)


if __name__ == "__main__":
    app()
