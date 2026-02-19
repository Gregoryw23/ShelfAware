from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    cognito_sub: str
    email: EmailStr
    status: str
    created_at: datetime
