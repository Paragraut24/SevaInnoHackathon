import pytest
from fastapi.testclient import TestClient

from app.limiter import limiter
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    limiter.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
