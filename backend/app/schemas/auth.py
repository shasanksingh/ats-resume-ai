from pydantic import BaseModel, Field

from app.schemas.resume import ApiModel


class AuthRequest(ApiModel):
    name: str | None = Field(default=None, max_length=120)
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(ApiModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile
