from pydantic import BaseModel
from app.schemas.user_out import UserOut

class RegisterResponse(BaseModel):
    message: str
    user_sub: str
    user_confirmed: bool