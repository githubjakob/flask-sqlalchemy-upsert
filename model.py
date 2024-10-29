import uuid
from typing import TypeVar
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class ModelForTest(Base):
    __tablename__ = "model_for_test"

    key: Mapped[str] = mapped_column(unique=True)
    data: Mapped[str] = mapped_column()


ModelType = TypeVar("ModelType", bound=Base)
