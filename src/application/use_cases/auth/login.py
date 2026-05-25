from pydantic import BaseModel, EmailStr


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class LoginOutput(BaseModel):
    token: str
    user_id: str
    user_name: str
    user_email: str
