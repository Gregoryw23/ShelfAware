import asyncio
import importlib
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi import Response

import app.main as main_module


def _run_lifespan_once(module):
    async def _runner():
        async with module.lifespan(module.app):
            pass

    asyncio.run(_runner())


def test_spa_staticfiles_serves_existing_file(tmp_path):
    (tmp_path / "index.html").write_text("<html>index</html>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('ok')", encoding="utf-8")

    static_files = main_module.SPAStaticFiles(directory=str(tmp_path))
    scope = {"type": "http", "method": "GET", "path": "/app.js", "headers": []}

    response = asyncio.run(static_files.get_response("app.js", scope))

    assert response.status_code == 200
    assert str(response.path).endswith("app.js")


def test_spa_staticfiles_falls_back_to_index_for_missing_path(tmp_path):
    (tmp_path / "index.html").write_text("<html>index</html>", encoding="utf-8")

    static_files = main_module.SPAStaticFiles(directory=str(tmp_path))
    scope = {"type": "http", "method": "GET", "path": "/missing", "headers": []}

    with patch(
        "fastapi.staticfiles.StaticFiles.get_response",
        side_effect=[HTTPException(status_code=404, detail="Not Found"), Response(status_code=200)],
    ):
        response = asyncio.run(static_files.get_response("missing", scope))

    assert response.status_code == 200


def test_spa_staticfiles_reraises_non_404_errors(tmp_path):
    (tmp_path / "index.html").write_text("<html>index</html>", encoding="utf-8")
    static_files = main_module.SPAStaticFiles(directory=str(tmp_path))
    scope = {"type": "http", "method": "GET", "path": "/x", "headers": []}

    with patch("fastapi.staticfiles.StaticFiles.get_response", side_effect=HTTPException(status_code=500, detail="boom")):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(static_files.get_response("x", scope))

    assert exc.value.status_code == 500


def test_lifespan_starts_and_stops_scheduler_when_api_key_set(monkeypatch):
    scheduler = Mock()
    monkeypatch.setattr(main_module, "SynopsisScheduler", scheduler)
    monkeypatch.setattr(main_module.os, "getenv", lambda key, default=None: "test-key" if key == "OPENAI_API_KEY" else default)

    _run_lifespan_once(main_module)

    scheduler.initialize.assert_called_once_with(openai_api_key="test-key")
    scheduler.start.assert_called_once_with(hour=0, minute=0)
    scheduler.stop.assert_called_once()


def test_lifespan_logs_warning_when_scheduler_missing(monkeypatch):
    monkeypatch.setattr(main_module, "SynopsisScheduler", None)

    _run_lifespan_once(main_module)


def test_lifespan_no_api_key_skips_scheduler_start(monkeypatch):
    scheduler = Mock()
    monkeypatch.setattr(main_module, "SynopsisScheduler", scheduler)
    monkeypatch.setattr(main_module.os, "getenv", lambda key, default=None: None)

    _run_lifespan_once(main_module)

    scheduler.initialize.assert_not_called()
    scheduler.start.assert_not_called()
    scheduler.stop.assert_called_once()


def test_lifespan_catches_startup_exception(monkeypatch):
    scheduler = Mock()
    scheduler.start.side_effect = Exception("startup failed")
    monkeypatch.setattr(main_module, "SynopsisScheduler", scheduler)
    monkeypatch.setattr(main_module.os, "getenv", lambda key, default=None: "test-key" if key == "OPENAI_API_KEY" else default)

    _run_lifespan_once(main_module)

    scheduler.stop.assert_called_once()


def test_trigger_manual_sync_returns_error_when_scheduler_missing(monkeypatch):
    monkeypatch.setattr(main_module, "SynopsisScheduler", None)

    result = main_module.trigger_manual_sync()

    assert result["status"] == "error"
    assert "not available" in result["message"]


def test_trigger_manual_sync_success(monkeypatch):
    scheduler = Mock()
    scheduler.add_manual_job.return_value = {"job": "ok"}
    monkeypatch.setattr(main_module, "SynopsisScheduler", scheduler)

    result = main_module.trigger_manual_sync()

    assert result == {"status": "success", "data": {"job": "ok"}}


def test_trigger_manual_sync_handles_exception(monkeypatch):
    scheduler = Mock()
    scheduler.add_manual_job.side_effect = Exception("boom")
    monkeypatch.setattr(main_module, "SynopsisScheduler", scheduler)

    result = main_module.trigger_manual_sync()

    assert result["status"] == "error"
    assert result["message"] == "boom"


def test_main_module_creates_static_dir_when_missing(monkeypatch):
    Path("app/static").mkdir(parents=True, exist_ok=True)

    makedirs_mock = Mock()
    monkeypatch.setattr(main_module.os.path, "exists", lambda path: False)
    monkeypatch.setattr(main_module.os, "makedirs", makedirs_mock)

    importlib.reload(main_module)

    makedirs_mock.assert_called_once_with("app/static")
