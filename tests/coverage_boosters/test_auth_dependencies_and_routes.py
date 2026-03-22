from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import auth as auth_deps
from app.models.user import User
from app.routes import auth as auth_routes


def test_get_current_user_missing_credentials():
    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_user(None)
    assert exc.value.status_code == 401


def test_get_current_user_invalid_token(monkeypatch):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")

    class _Svc:
        def validate_token(self, _):
            raise RuntimeError("bad token")

    monkeypatch.setattr(auth_deps, "CognitoService", lambda: _Svc())

    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_user(creds)
    assert exc.value.status_code == 401


def test_get_current_user_success(monkeypatch):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good-token")

    class _Svc:
        def validate_token(self, _):
            return {"sub": "abc"}

    monkeypatch.setattr(auth_deps, "CognitoService", lambda: _Svc())

    claims = auth_deps.get_current_user(creds)
    assert claims["sub"] == "abc"


def test_get_current_db_user_missing_sub(db):
    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_db_user(db, {"email": "x@test.com"})
    assert exc.value.status_code == 401


def test_get_current_db_user_not_found(db):
    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_db_user(db, {"sub": "missing"})
    assert exc.value.status_code == 401


def test_get_current_db_user_success(db):
    user = User(email="dep@test.com", cognito_sub="sub-123")
    db.add(user)
    db.commit()

    resolved = auth_deps.get_current_db_user(db, {"sub": "sub-123"})
    assert resolved.email == "dep@test.com"


def test_auth_register_integrity_error_path(monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from app.schemas.user_create import UserCreate

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.commit.side_effect = IntegrityError("stmt", "params", Exception("dup"))

    monkeypatch.setattr(
        auth_routes.cognito_service,
        "register_user",
        lambda **kwargs: {"UserSub": "sub-1", "UserConfirmed": False},
    )

    payload = UserCreate(username="tester", email="tester@example.com", password="Password123!")

    with pytest.raises(HTTPException) as exc:
        auth_routes.register(payload, db)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()


def test_auth_login_profile_commit_integrity_error_path(monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from app.schemas.user_login import UserLogin

    user = User(email="login2@example.com", cognito_sub="sub-login2")

    db = MagicMock()
    q1 = MagicMock()
    q1.filter.return_value.first.return_value = user
    q2 = MagicMock()
    q2.filter.return_value.first.return_value = None
    db.query.side_effect = [q1, q2]
    db.commit.side_effect = IntegrityError("stmt", "params", Exception("profile dup"))

    monkeypatch.setattr(
        auth_routes.cognito_service,
        "authenticate_user",
        lambda **kwargs: {"access_token": "a", "id_token": "i", "refresh_token": "r"},
    )

    payload = UserLogin(email="login2@example.com", password="Password123!")
    result = auth_routes.login(payload, db)

    assert result["message"] == "Login successful"
    db.rollback.assert_called_once()
