from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
from contextlib import asynccontextmanager

from database import Database, init_database
from auth import AuthService
from sessions import SessionService
from models import UserCreate, UserLogin, SessionResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Study Room API",
    description="网络自习室后端API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
auth_service = AuthService()
session_service = SessionService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    user_id = await auth_service.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    try:
        await auth_service.create_user(user.name, user.password)
        return {"message": "User created successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@app.post("/api/login")
async def login(user: UserLogin):
    """Login user and return JWT token"""
    token = await auth_service.authenticate_user(user.name, user.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return {"token": token}


@app.post("/api/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(user_id: int = Depends(get_current_user)):
    """Create a new desktop session"""
    try:
        session = await session_service.create_session(user_id)
        return session
    except ValueError as e:
        if "already has an active session" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/sessions/me")
async def get_my_session(user_id: int = Depends(get_current_user)):
    """Get current user's session"""
    session = await session_service.get_user_session(user_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    return session


@app.delete("/api/sessions/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_session(user_id: int = Depends(get_current_user)):
    """Delete current user's session"""
    success = await session_service.delete_session(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )


@app.post("/api/sessions/me/extend")
async def extend_my_session(user_id: int = Depends(get_current_user)):
    """Extend current user's session by 30 minutes"""
    success = await session_service.extend_session(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    return {"message": "Session extended successfully"}


@app.get("/api/sessions/all")
async def get_all_sessions():
    """Get all active sessions (for the grid view)"""
    sessions = await session_service.get_all_sessions()
    return {"sessions": sessions, "total": len(sessions), "max_capacity": 50}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
