from pydantic import BaseModel, EmailStr


class RegisterInput(BaseModel):
    user_name: str
    email: EmailStr
    password: str


class RegisterOutput(BaseModel):
    user_id: str
    user_name: str
    user_email: str
