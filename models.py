from pydantic import BaseModel


class LoginUser(BaseModel):
    email: str
    password: str


class SignUpUser(LoginUser):
    name: str

class CL(BaseModel):
    job_description: str
    user_id: int