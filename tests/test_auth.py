import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import mock_open, patch

import pytest
from fastapi import HTTPException
from jose import jwt

from unicef_geospatial.utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    Token,
    TokenData,
    User,
    UserInDB,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user,
    get_users,
    verify_password,
)


class TestGetUsers:
    """Test cases for the get_users function."""

    @patch.dict(os.environ, {"PATH_TO_USERS_FILE": "/path/to/users.json"})
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"username": "testuser", "hashed_password": "hash123"}]',
    )
    def test_get_users_success(self, mock_open):
        """Test successful loading of users from file."""
        users = get_users()
        assert len(users) == 1
        assert users[0]["username"] == "testuser"
        assert users[0]["hashed_password"] == "hash123"

    @patch.dict(os.environ, {"PATH_TO_USERS_FILE": "/nonexistent/path.json"})
    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_get_users_file_not_found(self, mock_open):
        """Test get_users returns empty list when file not found."""
        users = get_users()
        assert users == []

    @patch.dict(os.environ, {"PATH_TO_USERS_FILE": "/path/to/users.json"})
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_get_users_invalid_json(self, mock_open):
        """Test get_users handles invalid JSON gracefully."""
        with pytest.raises(json.JSONDecodeError):
            get_users()


class TestGetUser:
    """Test cases for the get_user function."""

    @patch("unicef_geospatial.utils.auth.get_users")
    def test_get_user_exists(self, mock_get_users):
        """Test getting an existing user."""
        mock_get_users.return_value = [
            {"username": "user1", "hashed_password": "hash1"},
            {"username": "user2", "hashed_password": "hash2"},
        ]

        user = get_user("user1")
        assert user is not None
        assert isinstance(user, UserInDB)
        assert user.username == "user1"
        assert user.hashed_password == "hash1"

    @patch("unicef_geospatial.utils.auth.get_users")
    def test_get_user_not_exists(self, mock_get_users):
        """Test getting a non-existent user."""
        mock_get_users.return_value = [
            {"username": "user1", "hashed_password": "hash1"},
        ]

        user = get_user("nonexistent")
        assert user is None

    @patch("unicef_geospatial.utils.auth.get_users")
    def test_get_user_empty_users(self, mock_get_users):
        """Test getting user when no users exist."""
        mock_get_users.return_value = []

        user = get_user("anyuser")
        assert user is None


class TestVerifyPassword:
    """Test cases for the verify_password function."""

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        result = verify_password(hashed_password, password)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword"
        wrong_password = "wrongpassword"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        result = verify_password(hashed_password, wrong_password)
        assert result is False

    def test_verify_password_empty_strings(self):
        """Test password verification with empty strings."""
        empty_hash = hashlib.sha256("".encode()).hexdigest()

        result = verify_password(empty_hash, "")
        assert result is True

    def test_verify_password_special_characters(self):
        """Test password verification with special characters."""
        password = "p@ssw0rd!#$%"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        result = verify_password(hashed_password, password)
        assert result is True


class TestAuthenticateUser:
    """Test cases for the authenticate_user function."""

    @patch("unicef_geospatial.utils.auth.get_user")
    def test_authenticate_user_success(self, mock_get_user):
        """Test successful user authentication."""
        password = "testpass"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        mock_user = UserInDB(username="testuser", hashed_password=hashed_password)
        mock_get_user.return_value = mock_user

        user = authenticate_user("testuser", password)
        assert user is not None
        assert isinstance(user, User)
        assert user.username == "testuser"

    @patch("unicef_geospatial.utils.auth.get_user")
    def test_authenticate_user_not_found(self, mock_get_user):
        """Test authentication with non-existent user."""
        mock_get_user.return_value = None

        user = authenticate_user("nonexistent", "password")
        assert user is None

    @patch("unicef_geospatial.utils.auth.get_user")
    def test_authenticate_user_wrong_password(self, mock_get_user):
        """Test authentication with wrong password."""
        password = "correctpass"
        wrong_password = "wrongpass"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        mock_user = UserInDB(username="testuser", hashed_password=hashed_password)
        mock_get_user.return_value = mock_user

        user = authenticate_user("testuser", wrong_password)
        assert user is None


class TestCreateAccessToken:
    """Test cases for the create_access_token function."""

    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

        expected_exp = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        actual_exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        time_diff = abs((expected_exp - actual_exp).total_seconds())
        assert time_diff < 60

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "testuser"}
        custom_expiry = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=custom_expiry)

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == "testuser"

        expected_exp = datetime.now(timezone.utc) + custom_expiry
        actual_exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        time_diff = abs((expected_exp - actual_exp).total_seconds())
        assert time_diff < 60

    def test_create_access_token_preserves_data(self):
        """Test that token creation preserves original data."""
        original_data = {
            "sub": "testuser",
            "role": "admin",
            "email": "test@example.com",
        }
        data_copy = original_data.copy()

        token = create_access_token(data_copy)

        assert original_data == {
            "sub": "testuser",
            "role": "admin",
            "email": "test@example.com",
        }

        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"
        assert decoded["email"] == "test@example.com"


class TestGetCurrentUser:
    """Test cases for the get_current_user function."""

    @patch("unicef_geospatial.utils.auth.get_user")
    def test_get_current_user_success(self, mock_get_user):
        """Test successful current user retrieval."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        mock_user = UserInDB(username="testuser", hashed_password="hash123")
        mock_get_user.return_value = mock_user

        user = asyncio.run(get_current_user(token))

        assert isinstance(user, User)
        assert user.username == "testuser"

    def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(invalid_token))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    def test_get_current_user_expired_token(self):
        """Test current user retrieval with expired token."""
        data = {"sub": "testuser"}
        expired_delta = timedelta(minutes=-1)
        expired_token = create_access_token(data, expires_delta=expired_delta)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(expired_token))

        assert exc_info.value.status_code == 401

    def test_get_current_user_missing_subject(self):
        """Test current user retrieval with token missing subject."""
        data = {"user": "testuser"}
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(token))

        assert exc_info.value.status_code == 401

    @patch("unicef_geospatial.utils.auth.get_user")
    def test_get_current_user_user_not_found(self, mock_get_user):
        """Test current user retrieval when user doesn't exist in database."""
        data = {"sub": "nonexistentuser"}
        token = create_access_token(data)

        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(token))

        assert exc_info.value.status_code == 401


class TestUserModels:
    """Test cases for user-related Pydantic models."""

    def test_token_model(self):
        """Test Token model creation and validation."""
        token = Token(
            access_token="test.token.here", token_type="bearer", username="testuser"
        )

        assert token.access_token == "test.token.here"
        assert token.token_type == "bearer"
        assert token.username == "testuser"

    def test_token_data_model(self):
        """Test TokenData model creation and validation."""
        token_data = TokenData(username="testuser")
        assert token_data.username == "testuser"

        token_data_none = TokenData()
        assert token_data_none.username is None

    def test_user_model(self):
        """Test User model creation and validation."""
        user = User(username="testuser")
        assert user.username == "testuser"

    def test_user_in_db_model(self):
        """Test UserInDB model creation and validation."""
        user_in_db = UserInDB(username="testuser", hashed_password="hash123")
        assert user_in_db.username == "testuser"
        assert user_in_db.hashed_password == "hash123"
