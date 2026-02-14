from datetime import datetime
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    email: EmailStr
    status: str
    created_at: datetime
