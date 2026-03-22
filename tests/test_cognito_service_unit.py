import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.security import HTTPAuthorizationCredentials
from botocore.exceptions import ClientError
from jose import jwt
import requests

from app.services.cognito_service import CognitoService, RoleChecker
from app.exceptions import ServiceException


# Create exception classes for mocking Cognito service exceptions
class CodeMismatchException(Exception):
    pass


class ExpiredCodeException(Exception):
    pass


class InvalidPasswordException(Exception):
    pass


class UserNotFoundException(Exception):
    pass


class UserNotConfirmedException(Exception):
    pass


class NotAuthorizedException(Exception):
    pass


class UsernameExistsException(Exception):
    pass


@pytest.fixture
def cognito_service():
    """Create CognitoService instance with mocked environment variables."""
    with patch.dict(
        "os.environ",
        {
            "COGNITO_REGION": "us-east-1",
            "COGNITO_USER_POOL_ID": "us-east-1_test123",
            "COGNITO_CLIENT_ID": "test_client_id",
            "COGNITO_CLIENT_SECRET": "test_secret",
        },
    ):
        service = CognitoService()
        service._client = Mock()  # Mock the boto3 client
        
        # Set up the exceptions attribute on the client with proper exception classes
        exceptions_mock = Mock()
        exceptions_mock.CodeMismatchException = CodeMismatchException
        exceptions_mock.ExpiredCodeException = ExpiredCodeException
        exceptions_mock.InvalidPasswordException = InvalidPasswordException
        exceptions_mock.UserNotFoundException = UserNotFoundException
        exceptions_mock.NotAuthorizedException = NotAuthorizedException
        exceptions_mock.UserNotConfirmedException = UserNotConfirmedException
        exceptions_mock.UsernameExistsException = UsernameExistsException
        
        service._client.exceptions = exceptions_mock
        return service


class TestGetCognitoJwks:
    """Test JWKS fetching with requests library."""

    def test_get_cognito_jwks_success(self, cognito_service):
        """Test successful JWKS retrieval."""
        with patch("app.services.cognito_service.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "keys": [{"kid": "key1", "alg": "RS256"}]
            }
            mock_get.return_value = mock_response

            result = cognito_service._get_cognito_jwks()
            assert result == [{"kid": "key1", "alg": "RS256"}]

    def test_get_cognito_jwks_non_200_status(self, cognito_service):
        """Test JWKS retrieval with non-200 status code (line 55)."""
        with patch("app.services.cognito_service.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            with pytest.raises(ServiceException) as exc_info:
                cognito_service._get_cognito_jwks()
            assert exc_info.value.status_code == 500
            assert "Unable to fetch JWKS" in exc_info.value.detail

    def test_get_cognito_jwks_request_exception(self, cognito_service):
        """Test JWKS retrieval with request exception (line 57-59)."""
        with patch("app.services.cognito_service.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")

            result = cognito_service._get_cognito_jwks()
            assert result == []


class TestValidateToken:
    """Test JWT token validation."""

    def test_validate_token_success(self, cognito_service):
        """Test successful token validation."""
        with patch("app.services.cognito_service.jwt.get_unverified_header") as mock_header:
            with patch("app.services.cognito_service.jwt.decode") as mock_decode:
                cognito_service._jwks_keys = [
                    {"kid": "key1", "alg": "RS256", "n": "modulus", "e": "exponent"}
                ]
                
                mock_header.return_value = {"kid": "key1"}
                mock_decode.return_value = {"sub": "user123", "email": "test@example.com"}

                auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
                result = cognito_service.validate_token(auth)

                assert result["sub"] == "user123"
                assert result["email"] == "test@example.com"

    def test_validate_token_no_matching_key(self, cognito_service):
        """Test token validation when kid doesn't match any key (line 90)."""
        with patch("app.services.cognito_service.jwt.get_unverified_header") as mock_header:
            cognito_service._jwks_keys = [
                {"kid": "key1", "alg": "RS256"}
            ]
            
            mock_header.return_value = {"kid": "unknown_key"}

            auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
            
            with pytest.raises(ServiceException) as exc_info:
                cognito_service.validate_token(auth)
            assert exc_info.value.status_code == 401
            assert "Invalid token signature" in exc_info.value.detail

    def test_validate_token_expired(self, cognito_service):
        """Test token validation with expired token."""
        with patch("app.services.cognito_service.jwt.get_unverified_header") as mock_header:
            with patch("app.services.cognito_service.jwt.decode") as mock_decode:
                cognito_service._jwks_keys = [{"kid": "key1", "alg": "RS256"}]
                
                mock_header.return_value = {"kid": "key1"}
                mock_decode.side_effect = jwt.ExpiredSignatureError("Expired")

                auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired_token")
                
                with pytest.raises(ServiceException) as exc_info:
                    cognito_service.validate_token(auth)
                assert exc_info.value.status_code == 401
                assert "Token has expired" in exc_info.value.detail

    def test_validate_token_jwt_error(self, cognito_service):
        """Test token validation with JWT error."""
        with patch("app.services.cognito_service.jwt.get_unverified_header") as mock_header:
            with patch("app.services.cognito_service.jwt.decode") as mock_decode:
                cognito_service._jwks_keys = [{"kid": "key1", "alg": "RS256"}]
                
                mock_header.return_value = {"kid": "key1"}
                mock_decode.side_effect = jwt.JWTError("Invalid token")

                auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
                
                with pytest.raises(ServiceException) as exc_info:
                    cognito_service.validate_token(auth)
                assert exc_info.value.status_code == 401
                assert "Token validation error" in exc_info.value.detail


class TestConfirmForgotPassword:
    """Test confirm forgot password flow."""

    def test_confirm_forgot_password_success(self, cognito_service):
        """Test successful password reset."""
        cognito_service.client.confirm_forgot_password.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        result = cognito_service.confirm_forgot_password(
            username="test_user",
            confirmation_code="123456",
            new_password="NewPass123!"
        )

        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        cognito_service.client.confirm_forgot_password.assert_called_once()

    def test_confirm_forgot_password_code_mismatch(self, cognito_service):
        """Test password reset with mismatched code (line 113-122)."""
        cognito_service.client.confirm_forgot_password.side_effect = CodeMismatchException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_forgot_password(
                username="test_user",
                confirmation_code="wrong_code",
                new_password="NewPass123!"
            )
        assert exc_info.value.status_code == 400
        assert "Invalid reset code" in exc_info.value.detail

    def test_confirm_forgot_password_expired_code(self, cognito_service):
        """Test password reset with expired code."""
        cognito_service.client.confirm_forgot_password.side_effect = ExpiredCodeException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_forgot_password(
                username="test_user",
                confirmation_code="expired_code",
                new_password="NewPass123!"
            )
        assert exc_info.value.status_code == 400
        assert "Reset code has expired" in exc_info.value.detail

    def test_confirm_forgot_password_invalid_password(self, cognito_service):
        """Test password reset with invalid password."""
        cognito_service.client.confirm_forgot_password.side_effect = InvalidPasswordException("Policy error")

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_forgot_password(
                username="test_user",
                confirmation_code="valid_code",
                new_password="weak"
            )
        assert exc_info.value.status_code == 400
        assert "Password does not meet policy" in exc_info.value.detail

    def test_confirm_forgot_password_user_not_found(self, cognito_service):
        """Test password reset with user not found."""
        cognito_service.client.confirm_forgot_password.side_effect = UserNotFoundException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_forgot_password(
                username="nonexistent_user",
                confirmation_code="code",
                new_password="NewPass123!"
            )
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_confirm_forgot_password_client_error(self, cognito_service):
        """Test password reset with generic ClientError."""
        cognito_service.client.confirm_forgot_password.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}},
            "confirm_forgot_password"
        )

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_forgot_password(
                username="test_user",
                confirmation_code="code",
                new_password="NewPass123!"
            )
        assert exc_info.value.status_code == 400


class TestCheckUserRole:
    """Test role checking."""

    def test_check_user_role_success(self, cognito_service):
        """Test successful role check (line 166-167)."""
        claims = {"cognito:groups": ["Users", "Admins"]}
        result = cognito_service.check_user_role(claims, "Admins")
        assert result is True

    def test_check_user_role_insufficient_permissions(self, cognito_service):
        """Test role check with insufficient permissions."""
        claims = {"cognito:groups": ["Users"]}
        
        with pytest.raises(ServiceException) as exc_info:
            cognito_service.check_user_role(claims, "Admins")
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    def test_check_user_role_exception(self, cognito_service):
        """Test role check with exception."""
        claims = None  # Invalid claims
        
        with pytest.raises(ServiceException) as exc_info:
            cognito_service.check_user_role(claims, "Admins")
        assert exc_info.value.status_code == 403


class TestConfirmUser:
    """Test user confirmation flow."""

    def test_confirm_user_success(self, cognito_service):
        """Test successful user confirmation."""
        cognito_service.client.confirm_sign_up.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        result = cognito_service.confirm_user(
            username="test_user",
            confirmation_code="123456"
        )

        assert result == "User confirmed successfully."
        cognito_service.client.confirm_sign_up.assert_called_once()

    def test_confirm_user_code_mismatch(self, cognito_service):
        """Test user confirmation with mismatched code (line 227-232)."""
        cognito_service.client.confirm_sign_up.side_effect = CodeMismatchException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_user(
                username="test_user",
                confirmation_code="wrong_code"
            )
        assert exc_info.value.status_code == 400
        assert "Invalid confirmation code" in exc_info.value.detail

    def test_confirm_user_expired_code(self, cognito_service):
        """Test user confirmation with expired code."""
        cognito_service.client.confirm_sign_up.side_effect = ExpiredCodeException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_user(
                username="test_user",
                confirmation_code="expired_code"
            )
        assert exc_info.value.status_code == 400
        assert "Confirmation code has expired" in exc_info.value.detail

    def test_confirm_user_not_found(self, cognito_service):
        """Test user confirmation with user not found."""
        cognito_service.client.confirm_sign_up.side_effect = UserNotFoundException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_user(
                username="nonexistent_user",
                confirmation_code="code"
            )
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_confirm_user_generic_error(self, cognito_service):
        """Test user confirmation with generic error (line 242)."""
        cognito_service.client.confirm_sign_up.side_effect = Exception("Unknown error")

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.confirm_user(
                username="test_user",
                confirmation_code="code"
            )
        assert exc_info.value.status_code == 500
        assert "Confirmation failed" in exc_info.value.detail


class TestAuthenticateUser:
    """Test user authentication."""

    def test_authenticate_user_success(self, cognito_service):
        """Test successful authentication."""
        cognito_service.client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "id_token_123",
                "AccessToken": "access_token_123",
                "RefreshToken": "refresh_token_123",
            }
        }

        result = cognito_service.authenticate_user(
            username="test_user",
            password="TestPass123!"
        )

        assert result["id_token"] == "id_token_123"
        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_123"

    def test_authenticate_user_not_authorized(self, cognito_service):
        """Test authentication with invalid credentials."""
        cognito_service.client.initiate_auth.side_effect = NotAuthorizedException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.authenticate_user(
                username="test_user",
                password="WrongPass"
            )
        assert exc_info.value.status_code == 401
        assert "Invalid username or password" in exc_info.value.detail

    def test_authenticate_user_not_confirmed(self, cognito_service):
        """Test authentication with unconfirmed user."""
        cognito_service.client.initiate_auth.side_effect = UserNotConfirmedException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.authenticate_user(
                username="test_user",
                password="TestPass123!"
            )
        assert exc_info.value.status_code == 403
        assert "User account not confirmed" in exc_info.value.detail

    def test_authenticate_user_generic_error(self, cognito_service):
        """Test authentication with generic error."""
        cognito_service.client.initiate_auth.side_effect = Exception("Unknown error")

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.authenticate_user(
                username="test_user",
                password="TestPass123!"
            )
        assert exc_info.value.status_code == 500
        assert "Authentication failed" in exc_info.value.detail


class TestRegisterUser:
    """Test user registration."""

    def test_register_user_success(self, cognito_service):
        """Test successful user registration."""
        cognito_service.client.sign_up.return_value = {
            "UserSub": "uuid-123",
            "CodeDeliveryDetails": {"Destination": "t***@example.com"},
        }

        result = cognito_service.register_user(
            username="test_user",
            email="test@example.com",
            password="TestPass123!"
        )

        assert result["UserSub"] == "uuid-123"
        cognito_service.client.sign_up.assert_called_once()

    def test_register_user_already_exists(self, cognito_service):
        """Test user registration with existing user."""
        cognito_service.client.sign_up.side_effect = UsernameExistsException()

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.register_user(
                username="existing_user",
                email="existing@example.com",
                password="TestPass123!"
            )
        assert exc_info.value.status_code == 400
        assert "User already exists" in exc_info.value.detail

    def test_register_user_generic_error(self, cognito_service):
        """Test user registration with generic error."""
        cognito_service.client.sign_up.side_effect = Exception("Unknown error")

        with pytest.raises(ServiceException) as exc_info:
            cognito_service.register_user(
                username="test_user",
                email="test@example.com",
                password="TestPass123!"
            )
        assert exc_info.value.status_code == 500
        assert "Registration failed" in exc_info.value.detail


class TestInitiateForgotPassword:
    """Test forgot password initiation."""

    def test_initiate_forgot_password_success(self, cognito_service):
        """Test successful forgot password initiation."""
        cognito_service.client.forgot_password.return_value = {
            "CodeDeliveryDetails": {"Destination": "t***@example.com"}
        }

        result = cognito_service.initiate_forgot_password(username="test_user")

        assert "CodeDeliveryDetails" in result
        cognito_service.client.forgot_password.assert_called_once()


class TestRoleChecker:
    """Test RoleChecker dependency."""

    def test_role_checker_success(self, cognito_service):
        """Test successful role check in RoleChecker."""
        with patch("app.services.cognito_service.CognitoService") as MockCognitoService:
            mock_service = Mock()
            MockCognitoService.return_value = mock_service
            mock_service.validate_token.return_value = {"cognito:groups": ["Admins"]}
            mock_service.check_user_role.return_value = True

            auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
            checker = RoleChecker(allowed_role="Admins")
            
            result = checker(auth=auth, cognito_service=mock_service)
            assert result == {"cognito:groups": ["Admins"]}

    def test_role_checker_no_auth(self):
        """Test role checker with no authentication."""
        checker = RoleChecker(allowed_role="Admins")
        mock_service = Mock()
        
        with pytest.raises(ServiceException) as exc_info:
            checker(auth=None, cognito_service=mock_service)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
