import asyncio

import pytest
from fastapi import HTTPException

from app.routes import admin as admin_routes


def test_admin_list_users_direct_call():
    assert admin_routes.list_users() == {"message": "Admin access granted"}


def test_admin_generate_community_reviews_missing_key(monkeypatch, db):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(admin_routes.generate_community_reviews(db))

    assert exc.value.status_code == 500


def test_admin_generate_community_reviews_success(monkeypatch, db):
    class _Svc:
        def __init__(self, openai_api_key):
            self.openai_api_key = openai_api_key

        def generate_all_community_reviews(self, _db):
            return {"status": "success", "updated": 1}

    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setattr(admin_routes, "SynopsisSyncService", _Svc)

    result = asyncio.run(admin_routes.generate_community_reviews(db))
    assert result["status"] == "success"


def test_admin_sync_synopses_alias(monkeypatch, db):
    async def _fake_generate(_db):
        return {"status": "success", "updated": 2}

    monkeypatch.setattr(admin_routes, "generate_community_reviews", _fake_generate)
    result = asyncio.run(admin_routes.sync_synopses_manual(db))
    assert result["updated"] == 2


def test_admin_moderation_list_accept_reject(monkeypatch, db):
    class _Svc:
        def __init__(self, openai_api_key):
            self.openai_api_key = openai_api_key

        def list_moderation_items(self, _db, status_filter="pending"):
            return [{"moderation_id": "m1", "status": status_filter}]

        def accept_moderation_item(self, _db, moderation_id):
            return {"moderation_id": moderation_id, "status": "accepted"}

        def reject_moderation_item(self, _db, moderation_id):
            return {"moderation_id": moderation_id, "status": "rejected"}

    monkeypatch.setattr(admin_routes, "SynopsisSyncService", _Svc)

    listed = admin_routes.list_synopsis_moderation(status="pending", db=db)
    accepted = admin_routes.accept_synopsis_moderation("m1", db)
    rejected = admin_routes.reject_synopsis_moderation("m2", db)

    assert listed["count"] == 1
    assert accepted["result"]["status"] == "accepted"
    assert rejected["result"]["status"] == "rejected"


def test_admin_accept_reject_not_found_errors(monkeypatch, db):
    class _Svc:
        def __init__(self, openai_api_key):
            self.openai_api_key = openai_api_key

        def accept_moderation_item(self, _db, _id):
            raise ValueError("missing")

        def reject_moderation_item(self, _db, _id):
            raise ValueError("missing")

    monkeypatch.setattr(admin_routes, "SynopsisSyncService", _Svc)

    with pytest.raises(HTTPException) as exc1:
        admin_routes.accept_synopsis_moderation("x", db)
    with pytest.raises(HTTPException) as exc2:
        admin_routes.reject_synopsis_moderation("x", db)

    assert exc1.value.status_code == 404
    assert exc2.value.status_code == 404
