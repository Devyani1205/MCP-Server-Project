from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..database import User, PendingUser, OTP, get_db
from ..config import settings
from .schema import UserCreate

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session):
    """Retrieve all users from the database."""
    return db.query(User).all()


import random
import string
from ..utils.email_service import send_otp_email

OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 3

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def create_otp_record(db: Session, email: str, purpose: str) -> str:
    # Invalidate previous OTPs for this email and purpose
    db.query(OTP).filter(OTP.email == email, OTP.purpose == purpose, OTP.verified == False).delete()
    
    otp_code = generate_otp()
    otp_record = OTP(
        email=email,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )
    db.add(otp_record)
    db.commit()
    return otp_code

def verify_otp_logic(db: Session, email: str, otp_code: str, purpose: str) -> bool:
    otp_record = db.query(OTP).filter(
        OTP.email == email,
        OTP.purpose == purpose,
        OTP.verified == False
    ).first()

    if not otp_record:
        return False

    if otp_record.expires_at < datetime.utcnow():
        db.delete(otp_record)
        db.commit()
        return False

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        db.delete(otp_record)
        db.commit()
        return False

    if otp_record.otp_code != otp_code:
        otp_record.attempts += 1
        db.commit()
        return False

    # OTP is valid
    otp_record.verified = True
    db.commit()
    return True

def initiate_registration(db: Session, user_data: UserCreate):
    # Check if user already exists in main table
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Store in PendingUser
    db.query(PendingUser).filter(PendingUser.email == user_data.email).delete()
    
    hashed_password = get_password_hash(user_data.password)
    pending_user = PendingUser(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        role=user_data.role.value,
        lab_name=user_data.lab_name
    )
    db.add(pending_user)
    
    # Create OTP
    otp = create_otp_record(db, user_data.email, "register")
    
    # Send Email
    send_otp_email(user_data.email, otp)
    db.commit()
    return True

def finalize_registration(db: Session, email: str, otp_code: str):
    if not verify_otp_logic(db, email, otp_code, "register"):
        return None

    pending = db.query(PendingUser).filter(PendingUser.email == email).first()
    if not pending:
        return None

    # Create actual user
    new_user = User(
        email=pending.email,
        name=pending.name,
        password_hash=pending.password_hash,
        role=pending.role,
        lab_name=pending.lab_name,
        is_verified=True
    )
    db.add(new_user)
    
    # Cleanup
    db.delete(pending)
    db.query(OTP).filter(OTP.email == email, OTP.purpose == "register").delete()
    db.commit()
    db.refresh(new_user)
    return new_user

def initiate_forgot_password(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        # For security, we don't throw error, but we return False to main route
        return False

    otp = create_otp_record(db, email, "forgot_password")
    send_otp_email(email, otp)
    return True

def finalize_password_reset(db: Session, email: str, otp_code: str, new_password: str):
    if not verify_otp_logic(db, email, otp_code, "forgot_password"):
        return False

    user = get_user_by_email(db, email)
    if not user:
        return False

    user.password_hash = get_password_hash(new_password)
    user.is_verified = True
    
    # Cleanup
    db.query(OTP).filter(OTP.email == email, OTP.purpose == "forgot_password").delete()
    db.commit()
    return True

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            auth.credentials, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )
        
    return user
