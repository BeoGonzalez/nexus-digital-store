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
    auth_provider: str = "Amazon Cognito"
    cognito_region: str
    cognito_user_pool_id: str
    cognito_app_client_id: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
