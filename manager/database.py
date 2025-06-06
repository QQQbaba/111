import aiosqlite
import os
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "/data/app.db"):
        self.db_path = db_path
        
    async def get_connection(self):
        """Get database connection"""
        return await aiosqlite.connect(self.db_path)
    
    async def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a query and return the last row id"""
        async with await self.get_connection() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row"""
        async with await self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        async with await self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
