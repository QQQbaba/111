import os
import time
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import db


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, user_id: int) -> str:
        """Create a JWT access token"""
        expire = int(time.time()) + (self.access_token_expire_hours * 3600)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[int]:
        """Verify a JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except JWTError:
            return None
    
    async def get_user_by_name(self, username: str) -> Optional[dict]:
        """Get user by username"""
        return await db.fetch_one(
            "SELECT id, name, pass FROM users WHERE name = ?",
            (username,)
        )
    
    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        return await db.fetch_one(
            "SELECT id, name FROM users WHERE id = ?",
            (user_id,)
        )
    
    async def create_user(self, username: str, password: str) -> int:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_name(username)
        if existing_user:
            raise ValueError("Username already exists")
        
        # Hash password and create user
        hashed_password = self.get_password_hash(password)
        user_id = await db.execute(
            "INSERT INTO users (name, pass) VALUES (?, ?)",
            (username, hashed_password)
        )
        return user_id
    
    async def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        user = await self.get_user_by_name(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["pass"]):
            return None
        
        access_token = self.create_access_token(user["id"])
        return access_token
