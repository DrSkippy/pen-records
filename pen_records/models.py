import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Maker(Base):
    __tablename__ = "makers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(240), unique=True)


class NibMaterial(Base):
    __tablename__ = "nib_materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Pen(TimestampMixin, Base):
    __tablename__ = "pens"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    model: Mapped[str] = mapped_column(String(240), index=True)
    maker_id: Mapped[int] = mapped_column(ForeignKey("makers.id"), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    acquired_on: Mapped[date] = mapped_column(Date, index=True)
    acquired_on_approximate: Mapped[bool] = mapped_column(Boolean, default=False)
    disposed_on: Mapped[date | None] = mapped_column(Date, index=True)
    disposed_on_approximate: Mapped[bool] = mapped_column(Boolean, default=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    legacy_import_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    import_payload: Mapped[dict | None] = mapped_column(JSON)
    maker: Mapped[Maker] = relationship(lazy="joined")
    source: Mapped[Source | None] = relationship(lazy="joined")
    nibs: Mapped[list[Nib]] = relationship(back_populates="pen", cascade="all, delete-orphan")
    installations: Mapped[list[NibInstallation]] = relationship(back_populates="pen", cascade="all, delete-orphan")
    notes: Mapped[list[PenNote]] = relationship(back_populates="pen", cascade="all, delete-orphan")
    images: Mapped[list[PenImage]] = relationship(back_populates="pen", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("purchase_price >= 0"),
        CheckConstraint("disposed_on IS NULL OR disposed_on >= acquired_on"),
    )


class Nib(TimestampMixin, Base):
    __tablename__ = "nibs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pen_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pens.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(240))
    material_id: Mapped[int] = mapped_column(ForeignKey("nib_materials.id"))
    size: Mapped[str | None] = mapped_column(String(40))
    is_original: Mapped[bool] = mapped_column(Boolean, default=False)
    pen: Mapped[Pen] = relationship(back_populates="nibs")
    material: Mapped[NibMaterial] = relationship(lazy="joined")
    installations: Mapped[list[NibInstallation]] = relationship(back_populates="nib", cascade="all, delete-orphan")
    __table_args__ = (
        Index(
            "uq_one_original_nib",
            "pen_id",
            unique=True,
            postgresql_where=is_original,
            sqlite_where=text("is_original = 1"),
        ),
    )


class NibInstallation(TimestampMixin, Base):
    __tablename__ = "nib_installations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pen_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pens.id", ondelete="CASCADE"))
    nib_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nibs.id", ondelete="CASCADE"))
    installed_on: Mapped[date | None] = mapped_column(Date)
    removed_on: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    pen: Mapped[Pen] = relationship(back_populates="installations")
    nib: Mapped[Nib] = relationship(back_populates="installations")
    __table_args__ = (
        Index(
            "uq_one_current_nib",
            "pen_id",
            unique=True,
            postgresql_where=is_current,
            sqlite_where=text("is_current = 1"),
        ),
    )


class PenNote(TimestampMixin, Base):
    __tablename__ = "pen_notes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pen_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pens.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    event_on: Mapped[date | None] = mapped_column(Date)
    pen: Mapped[Pen] = relationship(back_populates="notes")


class PenImage(TimestampMixin, Base):
    __tablename__ = "pen_images"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pen_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pens.id", ondelete="CASCADE"))
    filename: Mapped[str | None] = mapped_column(String(120), unique=True)
    thumbnail_filename: Mapped[str | None] = mapped_column(String(120), unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(80))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int | None] = mapped_column(Integer)
    caption: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    pen: Mapped[Pen] = relationship(back_populates="images")
    __table_args__ = (CheckConstraint("filename IS NOT NULL OR source_url IS NOT NULL"),)
