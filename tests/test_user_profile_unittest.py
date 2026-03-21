from app.main import app
from app.models.user import User

from app.models.user_profile import UserProfile
from app.dependencies.auth import get_current_db_user

def test_get_my_profile_auto_create(client, db):
    """Test GET profile auto-creates missing profile."""
    test_user = User(email="new_profile@example.com", cognito_sub="sub-new")
    db.add(test_user)
    db.commit()

    app.dependency_overrides[get_current_db_user] = lambda: test_user
    response = client.get("/user-profile/me")
    assert response.status_code == 200
    assert response.json()["display_name"] == "new_profile"


def test_patch_my_profile(client, db):
    """Test updating existing profile."""
    test_user = User(email="update@example.com", cognito_sub="sub-update")
    db.add(test_user)
    db.commit()

    profile = UserProfile(user_id=test_user.user_id, display_name="OldName")
    db.add(profile)
    db.commit()

    app.dependency_overrides[get_current_db_user] = lambda: test_user

    payload = {"display_name": "NewName", "bio": "Updated Bio"}
    response = client.patch("/user-profile/me", json=payload)
    assert response.status_code == 200
    assert response.json()["display_name"] == "NewName"
    assert response.json()["bio"] == "Updated Bio"


def test_patch_my_profile_auto_create(client, db):
    """Test updating profile when profile doesn't exist yet (auto-creates)."""
    # FIXED: The endpoint auto-creates the profile if it's missing, so it returns 200, not 404.
    test_user = User(email="noprofile@example.com", cognito_sub="sub-no")
    db.add(test_user)
    db.commit()

    app.dependency_overrides[get_current_db_user] = lambda: test_user

    payload = {"bio": "Trying to update"}
    response = client.patch("/user-profile/me", json=payload)

    assert response.status_code == 200
    assert response.json()["bio"] == "Trying to update"
    assert response.json()["display_name"] == "noprofile"


def test_public_profile_found(client, db):
    """Test viewing a public profile."""
    test_user = User(email="public@example.com", cognito_sub="sub-public")
    db.add(test_user)
    db.commit()

    profile = UserProfile(user_id=test_user.user_id, display_name="PublicStar", bio="Famous")
    db.add(profile)
    db.commit()

    response = client.get("/user-profile/public/PublicStar")
    assert response.status_code == 200
    assert response.json()["bio"] == "Famous"


def test_public_profile_not_found(client):
    """Test viewing a non-existent public profile."""
    response = client.get("/user-profile/public/GhostUser")
    assert response.status_code == 404