from pydantic import BaseModel, EmailStr

class ConfirmUser(BaseModel):
    email: EmailStr
    confirmation_code: str