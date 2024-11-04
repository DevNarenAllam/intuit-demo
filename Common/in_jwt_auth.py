from fastapi import HTTPException, status, Depends, Header
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from .in_config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    ALGORITHM,
)

from .in_schemas import User, Token
from .in_models import User as DBUser
from .in_database import get_session

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash a password.

    Args:
        password (str): The plain password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def authenticate_user(user_id: int, password: str) -> Token:
    """
    Authenticate a user by username and password.

    Args:
        fake_db (dict): The database of users.
        username (str): The username of the user.
        password (str): The plain password of the user.

    Returns:
        Token: The authenticated user token object if successful, raises HTTPException otherwise.
    """
    session = next(get_session())
    user = session.get(DBUser, user_id)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "req_count":0}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username, "req_count":0}, expires_delta=refresh_token_expires
    )
    # Assuming Token is a Pydantic model
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="JWT"
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create an access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (Optional[timedelta]): The expiration time of the token.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a refresh token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (Optional[timedelta]): The expiration time of the token.

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    x_access_token: str = Header(..., alias="X-Access-Token"),
    x_refresh_token: str = Header(..., alias="X-Refresh-Token"),
):
    """
    Retrieve the current user based on the provided access and refresh tokens.

    Args:
        access_token (str): The access token provided in the request header.
        refresh_token (str): The refresh token provided in the request header.

    Returns:
        User: The authenticated user object with updated tokens if necessary.

    Raises:
        HTTPException: If the access token or refresh token is missing, invalid, or expired.
    """
    new_access_token = None
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"X-Access-Token": None, "X-Refresh-Token": None},
    )

    # Check if both access and refresh tokens are provided
    if not x_access_token or not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token or refresh token is missing",
            headers={
                "X-Access-Token": x_access_token,
                "X-Refresh-Token": x_refresh_token,
            },
        )

    try:
        # Decode the access token
        payload = jwt.decode(x_access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        req_count: str = payload.get("req_count")
        if req_count > RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"X-Access-Token": x_access_token},
        else:
            
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token is invalid",
                headers={"X-Access-Token": x_access_token},
            )
    except JWTError:
        # If access token is invalid, try to decode the refresh token
        try:
            payload = jwt.decode(x_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token is invalid",
                    headers={"X-Refresh-Token": x_refresh_token},
                )
            # Create a new access token if the refresh token is valid
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            new_access_token = create_access_token(
                data={"sub": username}, expires_delta=access_token_expires
            )

        except JWTError:
            # If refresh token is also invalid, raise an exception
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is expired",
                headers={"X-Refresh-Token": None},
            )

    # Retrieve user information from the database
    session = next(get_session())
    user = session.get(DBUser, int(username))

    if user is None:
        raise credentials_exception

    user = User(**user.model_dump())
    # Update user object with new access token if it was generated
    if new_access_token:
        user.access_token = new_access_token
        user.refresh_token = x_refresh_token

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current active user.

    Args:
        current_user (User): The current user object.

    Returns:
        User: The current active user object.

    Raises:
        HTTPException: If the user is inactive.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
