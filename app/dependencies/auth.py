from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.cognito_service import CognitoService

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    cognito_service = CognitoService()

    try:
        claims = cognito_service.validate_token(credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return claims

def get_current_db_user(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user),
) -> User:
    sub = claims.get("sub")

    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub")

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found for this token")

    return user