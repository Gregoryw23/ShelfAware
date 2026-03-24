import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user, get_current_db_user
from app.models.user import User


# Tests for get_current_user
def test_get_current_user_raises_401_when_no_credentials():
    """Lines 14-17: credentials is None branch"""
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"

def test_get_current_user_raises_401_on_invalid_token():
    """Lines 22-25: exception from validate_token branch"""
    mock_credentials = Mock(spec=HTTPAuthorizationCredentials)

    with patch("app.dependencies.auth.CognitoService") as MockCognito:
        MockCognito.return_value.validate_token.side_effect = Exception("bad token")
        with pytest.raises(HTTPException) as exc:
            get_current_user(credentials=mock_credentials)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired token"

def test_get_current_user_returns_claims_on_success():
    """Lines 19-26: happy path returns claims"""
    mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
    fake_claims = {"sub": "cognito-sub-123"}

    with patch("app.dependencies.auth.CognitoService") as MockCognito:
        MockCognito.return_value.validate_token.return_value = fake_claims
        result = get_current_user(credentials=mock_credentials)
    assert result == fake_claims

#Test for get_current_db_user
def test_get_current_db_user_raises_401_when_sub_missing():
    """Lines 36-37: missing sub in claims"""
    mock_db = Mock(spec=Session)
    with pytest.raises(HTTPException) as exc:
        get_current_db_user(db=mock_db, claims={})
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token: missing sub"


def test_get_current_db_user_raises_401_when_user_not_found():
    """Lines 38-39: user not in DB"""
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_current_db_user(db=mock_db, claims={"sub": "cognito-sub-123"})
    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found for this token"


def test_get_current_db_user_returns_user_on_success():
    """Lines 40-45: happy path returns user"""
    mock_db = Mock(spec=Session)
    fake_user = Mock(spec=User)
    mock_db.query.return_value.filter.return_value.first.return_value = fake_user

    result = get_current_db_user(db=mock_db, claims={"sub": "cognito-sub-123"})
    assert result == fake_user