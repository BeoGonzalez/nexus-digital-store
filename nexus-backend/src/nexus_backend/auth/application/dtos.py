from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    is_admin: bool
    is_active: bool
    image: str | None = None

    model_config = {"from_attributes": True}


class AuthInfoResponse(BaseModel):
    neon_auth_url: str
    message: str
