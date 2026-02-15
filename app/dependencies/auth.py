from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.cognito_service import decode_and_verify_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    # Require token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials

    # Verify token + decode claims
    try:
        claims = decode_and_verify_token(token)
        # claims should include at least: sub, roles/groups
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 3) Normalize what your app considers a “current user”
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "roles": claims.get("roles", []),  # your service should map Cognito groups -> roles
        "claims": claims,
    }