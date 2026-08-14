from unittest.mock import patch

from typer.testing import CliRunner

from pen_records.cli import app


def test_cli_import_command(tmp_path):
    path = tmp_path / "pens.csv"
    path.write_text("header\n")
    with patch("pen_records.cli.import_csv", return_value={"created": 2, "skipped": 0}) as importer:
        result = CliRunner().invoke(app, [str(path), "--no-download-images"])
    assert result.exit_code == 0
    assert '"created": 2' in result.stdout
    assert importer.call_args.args[1] == path
    assert importer.call_args.args[2] is False
