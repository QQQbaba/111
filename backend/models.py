from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    name: str
    password: str


class User(BaseModel):
    id: int
    name: str


class SessionResponse(BaseModel):
    id: str
    user_id: int
    user_name: Optional[str] = None
    started: int
    expires: int
    vnc_url: Optional[str] = None
    status: str = "active"


class SessionCreate(BaseModel):
    user_id: int


class SessionExtend(BaseModel):
    minutes: int = 30
