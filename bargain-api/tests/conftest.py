"""Pytest configuration and shared fixtures for BargainHuntrs API tests.

Environment variables are set BEFORE any application imports so that the
Pydantic ``Settings`` singleton picks up test-friendly values (no auto-scan,
a known JWT secret, a configured Amazon affiliate tag, etc.).
"""
import os
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

# ── Set env vars BEFORE importing the app ───────────────────────────────
os.environ.setdefault("AUTO_SCAN", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_bargain.db")
os.environ.setdefault("AMAZON_ASSOCIATES_TAG", "bargainhuntrs-20")
os.environ.setdefault("RESEND_API_KEY", "")  # console-only email in tests

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.db.models import User

# ── Mock database session ──────────────────────────────────────────────
class MockQuery:
    """Reconfigurable mock for SQLAlchemy Query chains.

    All filter/order_by/limit calls return ``self`` so the chain can be
    configured with a single ``first_return`` / ``all_return`` value.
    """

    def __init__(self):
        self._first = None
        self._all = []

    def filter(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._all

    def limit(self, n):
        return self

    def offset(self, n):
        return self

    def order_by(self, *args):
        return self

    def count(self):
        return len(self._all)

    def update(self, *args, **kwargs):
        return 0

    def delete(self, *args, **kwargs):
        return 0


class MockDBSession:
    """Minimal stand-in for ``sqlalchemy.orm.Session``.

    Tracks objects added via ``add`` so that ``flush`` can assign default
    attributes (``id``, ``is_active``) that the real database would set.

    ``query(Model)`` returns a per-model ``MockQuery`` so that endpoints
    which look up more than one model in a single request (e.g. the current
    user via ``get_current_user`` *and* a separate resource by id) can be
    configured independently via ``first_return_for(Model)``. The shared
    ``first_return``/``all_return`` properties remain as a convenience for
    the common single-model case and are backed by the ``User`` query.
    """

    def __init__(self):
        self._query = MockQuery()  # backward-compatible default (acts as User's query)
        self._queries_by_model = {}
        self.added = []

    def query(self, model=None):
        if model is None or model is User:
            return self._query
        if model not in self._queries_by_model:
            self._queries_by_model[model] = MockQuery()
        return self._queries_by_model[model]

    def first_return_for(self, model, value):
        """Configure the ``.first()`` result for a specific model's query."""
        self.query(model)._first = value

    def all_return_for(self, model, value):
        """Configure the ``.all()`` result for a specific model's query."""
        self.query(model)._all = value

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    def flush(self, *args, **kwargs):
        for obj in self.added:
            if getattr(obj, "id", None) is None and hasattr(obj, "id"):
                obj.id = uuid.uuid4()
            if isinstance(obj, User) and getattr(obj, "is_active", None) is None:
                obj.is_active = True

    def commit(self, *args, **kwargs):
        # Routes typically call add() then commit() without an explicit
        # flush() — assign default ids here too so returned objects (and
        # any immediate follow-up lookups within the same test) behave like
        # a real session would after an insert.
        self.flush()

    def refresh(self, *args, **kwargs):
        pass

    def rollback(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    # ── convenience helpers for tests ───────────────────────────────────
    @property
    def first_return(self):
        return self._query._first

    @first_return.setter
    def first_return(self, value):
        self._query._first = value

    @property
    def all_return(self):
        return self._query._all

    @all_return.setter
    def all_return(self, value):
        self._query._all = value

    def reset(self):
        """Clear added objects and query results (call between requests)."""
        self.added = []
        self._query = MockQuery()
        self._queries_by_model = {}


@pytest.fixture
def db_mock():
    """Provide a fresh mock DB session for each test."""
    return MockDBSession()


@pytest.fixture
def client(db_mock):
    """FastAPI TestClient wired to use the mock DB session."""
    from app.main import app

    def override_get_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
