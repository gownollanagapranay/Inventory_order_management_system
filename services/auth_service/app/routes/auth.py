
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import User
from ..schemas import UserRegister, UserResponse, LoginRequest, TokenResponse
from ..security import hash_password, verify_password
from ..settings import settings, create_access_token
from ..dependencies import get_current_user, require_role


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    # Normalize the email address.
    email = str(user_data.email).lower()

    # Check whether the email is already registered.
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # Never store the original password.
    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        # Protect against duplicate registrations occurring
        # at nearly the same time.
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    return new_user



@router.post("/login", response_model=TokenResponse)
def login_user(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    email = str(login_data.email).lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Use the same error for unknown emails and wrong passwords.
    if user is None or not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }



@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


# this checks if the user is Admin or not
@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_role("admin"))
):
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "role": current_user.role
    }
