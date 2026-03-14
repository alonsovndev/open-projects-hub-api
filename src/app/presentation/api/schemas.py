from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, default="alonsonh94@gmail.com")
    password: str = Field(min_length=1, default="demo123!A")


class LoginResponse(BaseModel):
    token: str
    email: str
    displayName: str
    loggedInAt: str
