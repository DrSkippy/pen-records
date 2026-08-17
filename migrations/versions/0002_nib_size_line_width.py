"""Split physical nib size from writing line width."""
import re
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None
LINE_WIDTH_PATTERN = re.compile(r"(?<![A-Za-z0-9])(EF|MF|BB|F|M|B)(?![A-Za-z0-9])", re.IGNORECASE)

def cleaned_nib(value):
    description = " ".join((value or "").split())
    if description.casefold() == "nemosyne 0.6 italic":
        return "Nemosyne", "MF"
    match = LINE_WIDTH_PATTERN.search(description)
    if not match:
        return description or None, None
    cleaned = (description[:match.start()] + description[match.end():]).strip(" -")
    return " ".join(cleaned.split()) or None, match.group(1).upper()

def upgrade():
    columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns("nibs")}
    with op.batch_alter_table("nibs") as batch:
        if "size" in columns and "nib_size" not in columns:
            batch.alter_column("size", new_column_name="nib_size", existing_type=sa.String(40))
        if "line_width" not in columns:
            batch.add_column(sa.Column("line_width", sa.String(40), nullable=True))
        if not columns["description"]["nullable"]:
            batch.alter_column("description", existing_type=sa.String(240), nullable=True)
    bind = op.get_bind()
    for row in bind.execute(sa.text("SELECT id, description FROM nibs")):
        description, line_width = cleaned_nib(row.description)
        bind.execute(sa.text("UPDATE nibs SET description=:description, line_width=:line_width WHERE id=:id"), {"id": row.id, "description": description, "line_width": line_width})

def downgrade():
    bind = op.get_bind()
    bind.execute(sa.text("UPDATE nibs SET description=trim(coalesce(description, '') || ' ' || coalesce(line_width, ''))"))
    with op.batch_alter_table("nibs") as batch:
        batch.alter_column("description", existing_type=sa.String(240), nullable=False)
        batch.drop_column("line_width")
        batch.alter_column("nib_size", new_column_name="size", existing_type=sa.String(40))
