"""
Command-line interface (CLI) for the Lead Generation Pipeline.
"""

from pathlib import Path

import typer  # type: ignore

app = typer.Typer(help="Yellowbird Telemetry — Lead Generation Pipeline")


@app.command()
def from_apollo(input: Path, output: Path, dry_run: bool = False) -> None:
    """Process Apollo.io CSV export into verified CRM leads."""
    # TODO: wire io.from_apollo_csv → verify.HunterClient →
    #       scoring.assign_tier → io.write_leads_csv
    typer.echo("Stub for from_apollo command")


@app.command()
def from_sabi(input: Path, output: Path, dry_run: bool = False) -> None:
    """Process SABI XLSX export into scored CRM leads."""
    # TODO: wire io.from_sabi_xlsx → scoring.assign_tier →
    #       io.write_leads_csv (no Hunter needed — SABI has verified emails)
    typer.echo("Stub for from_sabi command")


@app.command()
def score(input: Path) -> None:
    """Re-score an existing yellowbird_leads.csv and print tier assignments."""
    # TODO: read existing CSV → Lead objects → scoring → print table
    typer.echo("Stub for score command")


if __name__ == "__main__":
    app()
