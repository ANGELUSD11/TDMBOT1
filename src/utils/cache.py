import redis.asyncio as redis_async
import os
import json
import logging

logger = logging.getLogger('discord')

class RedisCache:
    def __init__(self):
        self.redis = None
        
    async def connect(self):
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.redis = redis_async.from_url(redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info("✅ Connected to Redis Cache successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                self.redis = None
        else:
            logger.warning("⚠️ No REDIS_URL found. Running without caching layer.")
            
    async def get(self, key: str):
        if not self.redis:
            return None
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis GET Error: {e}")
        return None
        
    async def set(self, key: str, value, ttl: int = 3600):
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis SET Error: {e}")

# Instancia global del caché para exportar
redis_cache = RedisCache()
