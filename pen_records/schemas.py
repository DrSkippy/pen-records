import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Lookup(ORMModel):
    id: int
    name: str


class NibOut(ORMModel):
    id: uuid.UUID
    description: str
    material: Lookup
    size: str | None
    is_original: bool


class InstallationOut(ORMModel):
    id: uuid.UUID
    nib_id: uuid.UUID
    installed_on: date | None
    removed_on: date | None
    is_current: bool


class NoteOut(ORMModel):
    id: uuid.UUID
    text: str
    event_on: date | None
    created_at: datetime
    updated_at: datetime


class ImageOut(ORMModel):
    id: uuid.UUID
    url: str
    thumbnail_url: str
    caption: str | None
    sort_order: int


class PenOut(ORMModel):
    id: uuid.UUID
    model: str
    maker: Lookup
    source: Lookup | None
    acquired_on: date
    acquired_on_approximate: bool
    disposed_on: date | None
    disposed_on_approximate: bool
    purchase_price: Decimal
    currency: str
    nibs: list[NibOut] = []
    installations: list[InstallationOut] = []
    notes: list[NoteOut] = []
    images: list[ImageOut] = []


class NibInput(BaseModel):
    description: str = Field(min_length=1, max_length=240)
    material: str = Field(min_length=1, max_length=80)
    size: str | None = Field(default=None, max_length=40)
    installed_on: date | None = None


class PenCreate(BaseModel):
    model: str = Field(min_length=1, max_length=240)
    maker: str = Field(min_length=1, max_length=120)
    source: str | None = Field(default=None, max_length=240)
    acquired_on: date
    acquired_on_approximate: bool = False
    disposed_on: date | None = None
    disposed_on_approximate: bool = False
    purchase_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    original_nib: NibInput

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.disposed_on and self.disposed_on < self.acquired_on:
            raise ValueError("disposed_on cannot precede acquired_on")
        return self


class PenUpdate(BaseModel):
    model: str | None = Field(default=None, min_length=1, max_length=240)
    maker: str | None = Field(default=None, min_length=1, max_length=120)
    source: str | None = Field(default=None, max_length=240)
    acquired_on: date | None = None
    acquired_on_approximate: bool | None = None
    disposed_on: date | None = None
    clear_disposed_on: bool = False
    disposed_on_approximate: bool | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class NoteInput(BaseModel):
    text: str = Field(min_length=1)
    event_on: date | None = None


class InstallInput(BaseModel):
    installed_on: date | None = None
    previous_removed_on: date | None = None
