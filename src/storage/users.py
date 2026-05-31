import hashlib
import os
import secrets
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.storage.models import User
from src.storage.orm import Base


class UsernameAlreadyExistsError(Exception):
    pass


class UserStore:
    """
    Manages user registration and authentication backed by a SQLite database.
    """

    def __init__(self, path: str) -> None:
        db_path = Path(path) / "users.sqlite"
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        # Only creates the `users` table; other tables live in their own DBs.
        Base.metadata.create_all(self.engine, tables=[User.__table__])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Return ``"<salt_hex>:<dk_hex>"`` using PBKDF2-HMAC-SHA256.
        
        Args:
            password: The plaintext password to hash.
        Returns:
            A string containing the salt and derived key, separated by a colon.
        """
        
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return salt.hex() + ":" + dk.hex()

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        """
        Constant-time password verification against a stored hash.
        
        Args:
            password: The plaintext password to verify.
            stored: The stored hash in the format produced by _hash_password.
        Returns:
            True if the password is correct, False otherwise.
        """
        
        parts = stored.split(":", 1)
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        expected_dk = bytes.fromhex(parts[1])
        actual_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return secrets.compare_digest(actual_dk, expected_dk)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_user(self, username: str, password: str) -> User:
        """
        Register a new user and return the persisted User object (with id and api_key).

        Args:
            username: The desired username for the new user.
            password: The plaintext password for the new user.
        Returns:
            The persisted User object.
        """
        
        hashed = self._hash_password(password)
        api_key = secrets.token_hex(32)
        session = self.SessionLocal()
        try:
            user = User(username=username, hashed_password=hashed, api_key=api_key)
            session.add(user)
            session.commit()
            session.refresh(user)
            # Detach from session so attributes remain accessible after close.
            session.expunge(user)
            return user
        except IntegrityError:
            session.rollback()
            raise UsernameAlreadyExistsError(username)
        finally:
            session.close()

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """
        Return the User matching the given API key, or None.

        Args:
            api_key: The API key to search for.
        Returns:
            The User object if found, None otherwise.
        """
        
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.api_key == api_key).first()
            if user is not None:
                session.expunge(user)
            return user
        finally:
            session.close()

    def verify_credentials(self, username: str, password: str) -> Optional[User]:
        """
        Verify a username/password pair and return the User on success, or None.
        
        Args:
            username: The username to authenticate.
            password: The plaintext password to verify.
        Returns:
            The User object if authentication is successful, None otherwise.
        """
        
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user is None:
                return None
            if not self._verify_password(password, user.hashed_password):
                return None
            session.expunge(user)
            return user
        finally:
            session.close()
