import time
import uuid
import redis
from typing import Optional, List, Dict
from database import db
from models import SessionResponse


class SessionService:
    def __init__(self):
        self.redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
        self.session_duration = 30 * 60  # 30 minutes in seconds
        self.max_sessions = 50
    
    async def create_session(self, user_id: int) -> SessionResponse:
        """Create a new desktop session for user"""
        # Check if user already has an active session
        existing_session = await self.get_user_session(user_id)
        if existing_session:
            raise ValueError("User already has an active session")
        
        # Check if we've reached max capacity
        active_sessions = await self.get_all_sessions()
        if len(active_sessions) >= self.max_sessions:
            raise ValueError("Maximum capacity reached")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        current_time = int(time.time() * 1000)  # milliseconds
        expires_time = current_time + (self.session_duration * 1000)
        
        # Create session in database
        await db.execute("""
            INSERT INTO sessions (id, user_id, started, expires, status)
            VALUES (?, ?, ?, ?, 'creating')
        """, (session_id, user_id, current_time, expires_time))
        
        # Set heartbeat in Redis
        await self._set_heartbeat(session_id, user_id)
        
        # Trigger container creation (this would be handled by the manager service)
        await self._trigger_container_creation(session_id, user_id)
        
        # Get user name
        user = await db.fetch_one("SELECT name FROM users WHERE id = ?", (user_id,))
        user_name = user["name"] if user else None
        
        return SessionResponse(
            id=session_id,
            user_id=user_id,
            user_name=user_name,
            started=current_time,
            expires=expires_time,
            vnc_url=f"/ws/vnc/{session_id}",
            status="creating"
        )
    
    async def get_user_session(self, user_id: int) -> Optional[SessionResponse]:
        """Get active session for user"""
        session = await db.fetch_one("""
            SELECT s.*, u.name as user_name 
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.user_id = ? AND s.expires > ?
        """, (user_id, int(time.time() * 1000)))
        
        if not session:
            return None
        
        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            user_name=session["user_name"],
            started=session["started"],
            expires=session["expires"],
            vnc_url=f"/ws/vnc/{session['id']}",
            status=session["status"]
        )
    
    async def get_all_sessions(self) -> List[SessionResponse]:
        """Get all active sessions"""
        sessions = await db.fetch_all("""
            SELECT s.*, u.name as user_name 
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.expires > ?
            ORDER BY s.started DESC
        """, (int(time.time() * 1000),))
        
        return [
            SessionResponse(
                id=session["id"],
                user_id=session["user_id"],
                user_name=session["user_name"],
                started=session["started"],
                expires=session["expires"],
                vnc_url=f"/ws/vnc/{session['id']}",
                status=session["status"]
            )
            for session in sessions
        ]
    
    async def delete_session(self, user_id: int) -> bool:
        """Delete user's session"""
        session = await self.get_user_session(user_id)
        if not session:
            return False
        
        # Remove from database
        await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        # Remove heartbeat from Redis
        await self._remove_heartbeat(session.id)
        
        # Trigger container deletion
        await self._trigger_container_deletion(session.id)
        
        return True
    
    async def extend_session(self, user_id: int, minutes: int = 30) -> bool:
        """Extend user's session"""
        session = await self.get_user_session(user_id)
        if not session:
            return False
        
        new_expires = session.expires + (minutes * 60 * 1000)  # Convert to milliseconds
        
        await db.execute(
            "UPDATE sessions SET expires = ? WHERE user_id = ?",
            (new_expires, user_id)
        )
        
        # Update heartbeat
        await self._set_heartbeat(session.id, user_id)
        
        return True
    
    async def _set_heartbeat(self, session_id: str, user_id: int):
        """Set heartbeat in Redis"""
        try:
            self.redis_client.setex(
                f"session:{session_id}:heartbeat",
                self.session_duration + 60,  # Extra 60 seconds buffer
                user_id
            )
        except Exception as e:
            print(f"Failed to set heartbeat for session {session_id}: {e}")
    
    async def _remove_heartbeat(self, session_id: str):
        """Remove heartbeat from Redis"""
        try:
            self.redis_client.delete(f"session:{session_id}:heartbeat")
        except Exception as e:
            print(f"Failed to remove heartbeat for session {session_id}: {e}")
    
    async def _trigger_container_creation(self, session_id: str, user_id: int):
        """Trigger container creation via Redis message"""
        try:
            self.redis_client.publish("container:create", f"{session_id}:{user_id}")
        except Exception as e:
            print(f"Failed to trigger container creation for session {session_id}: {e}")
    
    async def _trigger_container_deletion(self, session_id: str):
        """Trigger container deletion via Redis message"""
        try:
            self.redis_client.publish("container:delete", session_id)
        except Exception as e:
            print(f"Failed to trigger container deletion for session {session_id}: {e}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (called by background task)"""
        current_time = int(time.time() * 1000)
        expired_sessions = await db.fetch_all(
            "SELECT id FROM sessions WHERE expires <= ?",
            (current_time,)
        )
        
        for session in expired_sessions:
            session_id = session["id"]
            await self._remove_heartbeat(session_id)
            await self._trigger_container_deletion(session_id)
        
        # Remove from database
        await db.execute("DELETE FROM sessions WHERE expires <= ?", (current_time,))
