from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re
from enum import Enum

class UserRole(str, Enum):
    doctor = "doctor"
    coordinator = "coordinator"
    lab = "lab"
    admin = "admin"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.doctor
    lab_name: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @model_validator(mode='after')
    def check_lab_name(self) -> 'UserCreate':
        if self.role == UserRole.lab and not self.lab_name:
            raise ValueError('lab_name is required for lab accounts')
        if self.role != UserRole.lab:
            self.lab_name = None
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int

    @model_validator(mode='after')
    def filter_lab_name(self) -> 'UserResponse':
        if self.role != UserRole.lab:
            self.lab_name = None
        return self

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)
