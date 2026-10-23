from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin


class Experiment(IdentityMixin, Base):
    __tablename__ = "experiments"
    account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("accounts.id"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("account_id", "fingerprint"),)
