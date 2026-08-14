import json
from pathlib import Path

import typer

from .database import SessionLocal
from .importer import import_csv

app = typer.Typer(no_args_is_help=True)


@app.command("import-csv")
def import_csv_command(path: Path, download_images: bool = True):
    """Idempotently import the legacy flat CSV."""
    with SessionLocal() as session:
        result = import_csv(session, path, download_images)
    typer.echo(json.dumps(result, indent=2))
