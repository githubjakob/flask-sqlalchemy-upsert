import uuid
from typing import TypeVar
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class Base(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class ModelForTest(Base):
    key: Mapped[str] = mapped_column(unique=True)
    data: Mapped[str] = mapped_column()


ModelType = TypeVar("ModelType", bound=Base)
