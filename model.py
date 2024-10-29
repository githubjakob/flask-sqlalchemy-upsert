import uuid
from typing import TypeVar
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class ModelForTest(Base):
    __tablename__ = "model_for_test"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(unique=True)
    data: Mapped[str] = mapped_column()


ModelType = TypeVar("ModelType", bound=Base)
