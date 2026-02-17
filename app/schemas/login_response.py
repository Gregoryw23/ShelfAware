from pydantic import BaseModel
from app.schemas.user_out import UserOut

class LoginResponse(BaseModel):
    message: str
    user: UserOut
    tokens: dict