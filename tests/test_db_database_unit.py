import pytest

from app.db import database


class _FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True



def test_get_db_yields_session_and_closes_on_completion(monkeypatch):
    fake_session = _FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    generator = database.get_db()
    yielded = next(generator)

    assert yielded is fake_session
    assert fake_session.closed is False

    with pytest.raises(StopIteration):
        next(generator)

    assert fake_session.closed is True


def test_get_db_closes_session_on_generator_error(monkeypatch):
    fake_session = _FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    generator = database.get_db()
    _ = next(generator)

    with pytest.raises(RuntimeError, match="boom"):
        generator.throw(RuntimeError("boom"))

    assert fake_session.closed is True
