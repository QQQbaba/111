import asyncio
import time
import redis
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    def __init__(self, database, container_manager):
        self.db = database
        self.container_manager = container_manager
        self.redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
        self.running = False
        self.check_interval = 30  # Check every 30 seconds
        
    async def start(self):
        """Start the heartbeat monitor"""
        self.running = True
        logger.info("Heartbeat Monitor started")
        
        try:
            while self.running:
                await self._check_expired_sessions()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {e}")
    
    async def stop(self):
        """Stop the heartbeat monitor"""
        self.running = False
        logger.info("Heartbeat Monitor stopped")
    
    async def _check_expired_sessions(self):
        """Check for expired sessions and clean them up"""
        try:
            current_time = int(time.time() * 1000)  # milliseconds
            
            # Get all active sessions
            sessions = await self.db.fetch_all(
                "SELECT id, user_id, expires FROM sessions WHERE expires > ?",
                (current_time - 600000,)  # Include sessions expired in last 10 minutes
            )
            
            expired_sessions = []
            heartbeat_expired_sessions = []
            
            for session in sessions:
                session_id = session['id']
                expires = session['expires']
                
                # Check if session has expired by time
                if expires <= current_time:
                    expired_sessions.append(session_id)
                    continue
                
                # Check Redis heartbeat
                heartbeat_key = f"session:{session_id}:heartbeat"
                heartbeat = self.redis_client.get(heartbeat_key)
                
                if not heartbeat:
                    # No heartbeat found, session is considered expired
                    heartbeat_expired_sessions.append(session_id)
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                logger.info(f"Cleaning up time-expired session: {session_id}")
                await self._cleanup_session(session_id)
            
            for session_id in heartbeat_expired_sessions:
                logger.info(f"Cleaning up heartbeat-expired session: {session_id}")
                await self._cleanup_session(session_id)
            
            if expired_sessions or heartbeat_expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions + heartbeat_expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Error checking expired sessions: {e}")
    
    async def _cleanup_session(self, session_id: str):
        """Clean up an expired session"""
        try:
            # Remove heartbeat from Redis
            heartbeat_key = f"session:{session_id}:heartbeat"
            self.redis_client.delete(heartbeat_key)
            
            # Trigger container deletion
            self.redis_client.publish("container:delete", session_id)
            
            # Remove from database
            await self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            logger.info(f"Session {session_id} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    async def _get_session_stats(self) -> Dict:
        """Get session statistics"""
        try:
            current_time = int(time.time() * 1000)
            
            # Count active sessions
            active_count = await self.db.fetch_one(
                "SELECT COUNT(*) as count FROM sessions WHERE expires > ?",
                (current_time,)
            )
            
            # Count total sessions (including recently expired)
            total_count = await self.db.fetch_one(
                "SELECT COUNT(*) as count FROM sessions WHERE expires > ?",
                (current_time - 3600000,)  # Last hour
            )
            
            return {
                'active_sessions': active_count['count'] if active_count else 0,
                'total_sessions_last_hour': total_count['count'] if total_count else 0,
                'max_capacity': 50,
                'timestamp': current_time
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                'active_sessions': 0,
                'total_sessions_last_hour': 0,
                'max_capacity': 50,
                'timestamp': int(time.time() * 1000)
            }
