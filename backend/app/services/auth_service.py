from sqlalchemy.orm import Session
from datetime import timedelta
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthenticationError
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def signup(self, user_data: UserCreate) -> Token:
        # Check if user exists
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise AuthenticationError("Email already registered")

        # Create user
        user = self.user_repo.create(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )

        # Create token
        access_token = create_access_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    def login(self, login_data: UserLogin) -> Token:
        # Get user
        user = self.user_repo.get_by_email(login_data.email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        # Create token
        access_token = create_access_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    def get_current_user(self, user_id: int) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        return UserResponse.model_validate(user)
