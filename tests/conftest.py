import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.services import order_service


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch):
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(
        order_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    yield

    Base.metadata.drop_all(bind=engine)