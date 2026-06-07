from pydantic import BaseModel


class MeOutput(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    active: bool
