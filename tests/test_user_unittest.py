from app.main import app

from app.models.user import User

# TEST ROUTES: /auth

# Test valid payload, successful registration
def test_auth_registration(client, mocker):
    mocker.patch(
        "app.routes.auth.cognito_service.register_user",
        return_value={"UserSub": "sub", "UserConfirmed": False},
    )
    payload = {
        "username": "test_user", 
        "email": "test@test.com", 
        "password": "Password123!"
    }
    response = client.post("/auth/registration", json=payload)
    assert response.status_code == 201

# Registering twice with the same email returns error 409
def test_duplicate_email_returns_409(client, mocker):
    mocker.patch(
        "app.routes.auth.cognito_service.register_user",
        return_value={"UserSub": "sub", "UserConfirmed": False},
    )
    payload = {
        "username": "test_user",
        "email": "test@test.com",
        "password": "Password123!"
    }
    client.post("/auth/registration", json=payload)
    response = client.post("/auth/registration", json=payload)
    assert response.status_code == 409

# Test Cognito service failure returns error 400
def test_cognito_failure_returns_error(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.register_user",
        side_effect=ServiceException(status_code=400, detail="Weak password")
    )
    response = client.post("/auth/registration", json={
        "username": "test_user",
        "email": "test@test.com",
        "password": "Password123!"
    })
    assert response.status_code == 400

# Test that if Cognito registration fails, the user is not created in the local DB
def test_db_not_written_when_cognito_fails(client, mocker, db):
    from app.exceptions import ServiceException
    from app.models.user import User
    mocker.patch(
        "app.routes.auth.cognito_service.register_user",
        side_effect=ServiceException(status_code=400, detail="Error")
    )
    client.post("/auth/registration", json={
        "username": "test_user",
        "email": "test@test.com",
        "password": "Password123!"
    })
    assert db.query(User).filter(User.email == "test@test.com").first() is None

# Test password and email validation errors return 422
def test_password_missing_uppercase(client):
    response = client.post("/auth/registration", json={
        "username": "test_user",
        "email": "test@test.com",
        "password": "password123!"   # no uppercase
    })
    assert response.status_code == 422

def test_password_missing_special_char(client):
    response = client.post("/auth/registration", json={
        "username": "test_user",
        "email": "test@test.com",
        "password": "Password123"    # no special char
    })
    assert response.status_code == 422

def test_username_too_short(client):
    response = client.post("/auth/registration", json={
        "username": "ab",            # min_length=3
        "email": "test@test.com",
        "password": "Password123!"
    })
    assert response.status_code == 422

def test_invalid_email_format(client):
    response = client.post("/auth/registration", json={
        "username": "test_user",
        "email": "notanemail",
        "password": "Password123!"
    })
    assert response.status_code == 422

# Test account confirmation
def test_auth_confirm(client, mocker):
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_user", 
        return_value=True
    )
    payload = {"email": "test@test.com", "confirmation_code": "123456"}
    response = client.post("/auth/confirm", json=payload)
    
    assert response.status_code == 200

#Test invalid confirmation code returns error
def test_auth_confirm_invalid_code(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_user",
        side_effect=ServiceException(status_code=400, detail="Invalid confirmation code")
    )
    payload = {"email": "test@test.com", "confirmation_code": "000000"}
    response = client.post("/auth/confirm", json=payload)
   
    assert response.status_code == 400

# Expired confirmation code
def test_auth_confirm_expired_code(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_user",
        side_effect=ServiceException(status_code=400, detail="Code has expired")
    )
    payload = {"email": "test@test.com", "confirmation_code": "123456"}
    response = client.post("/auth/confirm", json=payload)
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

# Already confirmed user
def test_auth_confirm_already_confirmed(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_user",
        side_effect=ServiceException(status_code=400, detail="User is already confirmed")
    )
    payload = {"email": "test@test.com", "confirmation_code": "123456"}
    response = client.post("/auth/confirm", json=payload)
    assert response.status_code == 400

#Test successful login
def test_auth_login_success(client, mocker, db):
    test_user = User(email="login@test.com", cognito_sub="sub-login")
    db.add(test_user)
    db.commit()

    mocker.patch(
        "app.routes.auth.cognito_service.authenticate_user",
        return_value={
            "access_token": "token1", 
            "id_token": "token2", 
            "refresh_token": "token3"}
    )
    payload = {"email": "login@test.com", "password": "Password123!"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    # Verify all three tokens are returned in the response
    assert "access_token" in response.json()["tokens"]
    assert "id_token" in response.json()["tokens"]
    assert "refresh_token" in response.json()["tokens"]

# Wrong password → Cognito rejects credentials
def test_auth_login_wrong_password(client, mocker, db):
    from app.exceptions import ServiceException
    test_user = User(email="login@test.com", cognito_sub="sub-login")
    db.add(test_user)
    db.commit()
    mocker.patch(
        "app.routes.auth.cognito_service.authenticate_user",
        side_effect=ServiceException(status_code=401, detail="Incorrect username or password")
    )
    response = client.post("/auth/login", json={
        "email": "login@test.com",
        "password": "WrongPass123!"
    })
    assert response.status_code == 401

# Cognito passes but user doesn't exist in local DB
def test_auth_login_user_not_in_db(client, mocker):
    mocker.patch(
        "app.routes.auth.cognito_service.authenticate_user",
        return_value={
            "access_token": "token1", 
            "id_token": "token2", 
            "refresh_token": "token3"}
    )
    payload = {"email": "ghost@test.com", "password": "Password123!"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 404

# Unconfirmed user tries to log in
def test_auth_login_unconfirmed_user(client, mocker, db):
    from app.exceptions import ServiceException
    test_user = User(email="unconfirmed@test.com", cognito_sub="sub-unconfirmed")
    db.add(test_user)
    db.commit()
    mocker.patch(
        "app.routes.auth.cognito_service.authenticate_user",
        side_effect=ServiceException(status_code=401, detail="User is not confirmed")
    )
    response = client.post("/auth/login", json={
        "email": "unconfirmed@test.com",
        "password": "Password123!"
    })
    assert response.status_code == 401

# Test forgot password request
def test_auth_forgot_password(client, mocker):
    mocker.patch(
        "app.routes.auth.cognito_service.initiate_forgot_password", 
        return_value=True
    )
    payload = {"email": "test@test.com"}
    response = client.post("/auth/forgot-password", json=payload)
    assert response.status_code == 200

# Test forgot password with unknown email (should not leak info)
def test_auth_forgot_password_unknown_email(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.initiate_forgot_password",
        side_effect=ServiceException(status_code=404, detail="User not found")
    )
    response = client.post("/auth/forgot-password", json={"email": "ghost@test.com"})
    assert response.status_code == 200 # must NOT return 404 — that leaks whether email exists

# Test succesful password reset
def test_auth_reset_password(client, mocker):
    mocker.patch("app.routes.auth.cognito_service.confirm_forgot_password", return_value=True)
    # FIXED: The route expects 'token', not 'confirmation_code' based on the schema usage
    payload = {"email": "test@test.com", "token": "123456", "new_password": "NewPassword123!"}
    response = client.post("/auth/reset-password", json=payload)
    assert response.status_code == 200

# Expired reset token
def test_auth_reset_password_expired_token(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_forgot_password",
        side_effect=ServiceException(status_code=400, detail="Token has expired")
    )
    payload = {"email": "test@test.com", "token": "000000", "new_password": "NewPassword123!"}
    response = client.post("/auth/reset-password", json=payload)
    assert response.status_code == 400

# Invalid/wrong token
def test_auth_reset_password_invalid_token(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_forgot_password",
        side_effect=ServiceException(status_code=400, detail="Invalid verification code")
    )
    payload = {"email": "test@test.com", "token": "wrong", "new_password": "NewPassword123!"}
    response = client.post("/auth/reset-password", json=payload)
    assert response.status_code == 400

# Schema rejects weak password before reaching the route → 422
def test_auth_reset_password_fails_schema_validation(client, mocker):
    payload = {"email": "test@test.com", "token": "123456", "new_password": "weak"}
    response = client.post("/auth/reset-password", json=payload)
    assert response.status_code == 422

# Schema passes but Cognito rejects the password policy → 400
def test_auth_reset_password_weak_new_password(client, mocker):
    from app.exceptions import ServiceException
    mocker.patch(
        "app.routes.auth.cognito_service.confirm_forgot_password",
        side_effect=ServiceException(status_code=400, detail="Password does not meet requirements")
    )
    # Passes schema validation but Cognito has stricter rules
    payload = {"email": "test@test.com", "token": "123456", "new_password": "Passes123!"}
    response = client.post("/auth/reset-password", json=payload)
    assert response.status_code == 400

