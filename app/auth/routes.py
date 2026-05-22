from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, User
from . import service, schema

router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: schema.UserCreate, db: Session = Depends(get_db)):
    service.initiate_registration(db, user)
    return {"message": "OTP sent to your email. Please verify your account."}

@router.post("/verify-register-otp", response_model=dict)
def verify_register_otp(data: schema.OTPVerify, db: Session = Depends(get_db)):
    user = service.finalize_registration(db, data.email, data.otp)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    return {"message": "User registered and verified successfully"}

@router.post("/login", response_model=schema.TokenResponse, response_model_exclude_none=True)
def login(credentials: schema.UserLogin, db: Session = Depends(get_db)):
    # Verify user exists
    user = service.get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )
    
    # Verify password
    if not service.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role
    }
    access_token = service.create_access_token(data=token_data)
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/forgot-password", response_model=dict)
def forgot_password(data: schema.ForgotPassword, db: Session = Depends(get_db)):
    service.initiate_forgot_password(db, data.email)
    # Always return success message for security (don't reveal if user exists)
    return {"message": "If your email is registered, a password reset OTP has been sent."}

@router.post("/reset-password", response_model=dict)
def reset_password(data: schema.ResetPassword, db: Session = Depends(get_db)):
    success = service.finalize_password_reset(db, data.email, data.otp, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=schema.UserResponse, response_model_exclude_none=True)
async def get_me(current_user: User = Depends(service.get_current_user)):
    """
    Protected endpoint to get current user details.
    """
    return current_user
