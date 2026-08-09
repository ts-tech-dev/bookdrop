import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # StaticPool keeps every connection on the same in-memory database; without it each
    # new connection (TestClient runs requests in a worker thread) would see an empty one.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Not entered as a context manager, so FastAPI's lifespan (init_db + scheduler) never
    # runs: routes hit the in-memory engine above via the get_db override regardless.
    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
