from fastapi.testclient import TestClient

from app.main import app


class _DummyScheduler:
    initialized = False
    started = False
    stopped = False

    @classmethod
    def initialize(cls, openai_api_key):
        cls.initialized = bool(openai_api_key)

    @classmethod
    def start(cls, hour=0, minute=0):
        cls.started = True

    @classmethod
    def stop(cls):
        cls.stopped = True

    @classmethod
    def add_manual_job(cls):
        return {"queued": True}


def test_home_and_favicon_routes_cover_main_handlers():
    with TestClient(app) as client:
        home = client.get("/")
        icon = client.get("/favicon.ico")

    assert home.status_code == 200
    assert home.json()["message"] == "Welcome to ShelfAware"
    assert icon.status_code == 204


def test_trigger_manual_sync_scheduler_missing(monkeypatch):
    import app.main as main_mod

    monkeypatch.setattr(main_mod, "SynopsisScheduler", None)
    with TestClient(app) as client:
        response = client.post("/admin/trigger-scheduler-sync")

    assert response.status_code == 200
    assert response.json()["status"] == "error"


def test_trigger_manual_sync_success(monkeypatch):
    import app.main as main_mod

    monkeypatch.setattr(main_mod, "SynopsisScheduler", _DummyScheduler)
    with TestClient(app) as client:
        response = client.post("/admin/trigger-scheduler-sync")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_trigger_manual_sync_exception_path(monkeypatch):
    import app.main as main_mod

    class _ExplodingScheduler:
        @classmethod
        def initialize(cls, openai_api_key):
            return None

        @classmethod
        def start(cls, hour=0, minute=0):
            return None

        @classmethod
        def stop(cls):
            return None

        @classmethod
        def add_manual_job(cls):
            raise RuntimeError("boom")

    monkeypatch.setattr(main_mod, "SynopsisScheduler", _ExplodingScheduler)

    with TestClient(app) as client:
        response = client.post("/admin/trigger-scheduler-sync")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert "boom" in payload["message"]


def test_lifespan_with_openai_key_starts_and_stops_scheduler(monkeypatch):
    import app.main as main_mod

    _DummyScheduler.started = False
    _DummyScheduler.stopped = False
    monkeypatch.setattr(main_mod, "SynopsisScheduler", _DummyScheduler)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with TestClient(app):
        pass

    assert _DummyScheduler.started is True
    assert _DummyScheduler.stopped is True


def test_lifespan_without_key_uses_disabled_branch(monkeypatch):
    import app.main as main_mod

    _DummyScheduler.started = False
    monkeypatch.setattr(main_mod, "SynopsisScheduler", _DummyScheduler)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with TestClient(app):
        pass

    assert _DummyScheduler.started is False
