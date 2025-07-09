import aiosqlite
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'aira.db'):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    channel_id TEXT,
                    anime_id INTEGER,
                    title TEXT,
                    episodes INTEGER DEFAULT 0,
                    PRIMARY KEY (channel_id, anime_id)
                )
            ''')
            await db.commit()

    async def add_subscription(self, channel_id: str, anime_id: int, title: str, episodes: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO subscriptions 
                (channel_id, anime_id, title, episodes)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, anime_id, title, episodes))
            await db.commit()

    async def remove_subscription(self, channel_id: str, anime_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM subscriptions 
                WHERE channel_id = ? AND anime_id = ?
                RETURNING *
            ''', (channel_id, anime_id))
            deleted = await cursor.fetchone()
            await db.commit()
            return deleted is not None

    async def remove_subscription_by_title(self, channel_id: str, title: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM subscriptions 
                WHERE channel_id = ? AND LOWER(title) = LOWER(?)
                RETURNING *
            ''', (channel_id, title))
            deleted = await cursor.fetchone()
            await db.commit()
            return deleted is not None

    async def remove_all_subscriptions(self, channel_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM subscriptions 
                WHERE channel_id = ?
                RETURNING *
            ''', (channel_id,))
            deleted = await cursor.fetchall()
            await db.commit()
            return len(deleted)

    async def get_channel_subscriptions(self, channel_id: str) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT anime_id as id, title, episodes 
                FROM subscriptions 
                WHERE channel_id = ?
            ''', (channel_id,))
            rows = await cursor.fetchall()
            return [{'id': row[0], 'title': row[1], 'episodes': row[2]} for row in rows]

    async def get_all_subscriptions(self) -> Dict[str, List[Dict]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT channel_id, anime_id as id, title, episodes 
                FROM subscriptions
            ''')
            rows = await cursor.fetchall()
            
            result = {}
            for row in rows:
                channel_id = row[0]
                if channel_id not in result:
                    result[channel_id] = []
                result[channel_id].append({
                    'id': row[1],
                    'title': row[2],
                    'episodes': row[3]
                })
            return result

    async def update_episodes(self, anime_id: int, episodes: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE subscriptions 
                SET episodes = ? 
                WHERE anime_id = ?
            ''', (episodes, anime_id))
            await db.commit() 