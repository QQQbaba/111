import aiosqlite
import os
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "/data/app.db"):
        self.db_path = db_path
        
    def get_connection(self):
        """Return an *awaitable* connection (do **not** await here)"""
        return aiosqlite.connect(self.db_path)
    
    async def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a query and return the last row id"""
        async with self.get_connection() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# Global database instance
db = Database()


async def init_database():
    """Initialize database with required tables"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db.db_path), exist_ok=True)

    async with aiosqlite.connect(db.db_path) as conn:
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                pass TEXT NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                started INTEGER NOT NULL,
                expires INTEGER NOT NULL,
                container_id TEXT,
                vnc_port INTEGER,
                status TEXT DEFAULT 'creating',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
        
        await conn.commit()
        print("Database initialized successfully")
