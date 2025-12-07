# src/core/redis.py

"""
Redis connection manager for session storage and caching
Handles JWT tokens, refresh tokens, and session management
"""

import json
from datetime import timedelta, timezone, datetime
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisManager:
    """
    Redis manager for handling connections and operations
    Implements singleton pattern
    """

    _pool: ConnectionPool | None = None
    _client: Redis | None = None

    @classmethod
    async def get_pool(cls) -> ConnectionPool:
        """Get or create Redis connection pool"""
        if cls._pool is None:
            logger.info("Creating Redis connection pool", url=settings.cache_url)
            cls._pool = ConnectionPool.from_url(
                settings.cache_url,
                max_connections=settings.redis_pool_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                decode_responses=True,
            )
            logger.info("Redis connection pool created")
        return cls._pool
    
    @classmethod
    async def get_client(cls) -> Redis:
        """Get or create Redis client"""
        if cls._client is None:
            pool = await cls.get_pool()
            cls._client = Redis(connection_pool=pool)
            logger.info("Redis client created")
        return cls._client
    
    @classmethod
    async def close(cls) -> None:
        """close redis connections"""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None

        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None

        logger.info("Redis connections closed")


class RedisService:
    """Service class for Redis operations."""

    def __init__(self):
        self.client: Redis | None = None

    async def _get_client(self) -> Redis:
        """Get Redis client instance."""
        if self.client is None:
            self.client = await RedisManager.get_client()
        return self.client
    
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            client = await self._get_client()
            return await client.ping()
        except RedisError as e:
            logger.error("Redis ping failed", error=str(e))
            return False
        
    # ==============================================================================
    # Basic Key-Value operations
    # ==============================================================================

    async def set(
        self, key: str, value: Any, expire: Optional[int] = None, serialize: bool = True
    ) -> bool:
        """
        Set a value in Redis

        Args:
            key: Redis key
            value: Value to store
            expire: Expiration time in seconds
            serialize: Whether to JSON serialize the value
        """
        try:
            client = await self._get_client()

            if serialize and not isinstance(value, (str, bytes)):
                value = json.dumps(value)

            if expire:
                return await client.setex(key, expire, value)
            else:
                return await client.set(key, value)
            
        except RedisError as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
        
    async def get(
        self, key: str, deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get a value from Redis

        Args:
            key: Redis key
            deserialize: Whether to JSON deserialize the value
        """
        try:
            client = await self._get_client()
            value = await client.get(key)

            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
                
            return value
        except RedisError as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return None
        
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        try:
            client = await self._get_client()
            return await client.delete(*keys)
        except RedisError as e:
            logger.error("Redis DELETE failed", keys=keys, error=str(e))
            return 0
        
    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        try:
            client = await self._get_client()
            return await client.exists(*keys)
        except RedisError as e:
            logger.error("Redis Exists failed", keys=keys, error=str(e))
            return 0
        
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        try:
            client = await self._get_client()
            return await client.expire(key, seconds)
        except RedisError as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
        
    # ==============================================================================
    # Session Management
    # ==============================================================================

    async def create_session(
        self, session_id: str, user_id: str, data: dict, expire_seconds: Optional[int] = None
    ) -> bool:
        """Create new session"""
        if expire_seconds is None:
            expire_seconds = settings.session_expire_seconds

        session_data = {
            "user_id": user_id,
            "created_at": str(datetime.now(timezone.utc)),
            **data
        }

        key = f"session:{session_id}"
        return await self.set(key, session_data, expire=expire_seconds)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = f"session:{session_id}"
        return await self.delete(key) > 0
    
    async def refresh_session(
        self, session_id: str, expire_seconds: Optional[int] = None,
    ) -> bool:
        """Refresh session expiration"""
        if expire_seconds is None:
            expire_seconds = settings.session_expire_seconds

        key = f"session:{session_id}"
        return await self.expire(key, expire_seconds)
    
    # ==============================================================================
    # Token Management (JWT and Refresh Tokens)
    # ==============================================================================

    async def store_refresh_token(
        self, token_id: str, user_id: str, expire_seconds: Optional[int] = None
    ) -> bool:
        """
        Store refresh token in whitelist

        Args:
            token_id: Unique token identifier (jti)
            user_id: User ID associated with token
            expire_seconds: Token expiration in seconds
        """
        if expire_seconds is None:
            expire_seconds = settings.refresh_token_expire_days * 86400

        key = f"refresh_token:{token_id}"
        value = {"user_id": user_id, "created_at": str(datetime.now(timezone.utc))}

        return await self.set(key, value, expire=expire_seconds)
    
    async def verify_refresh_token(self, token_id: str) -> Optional[dict]:
        """verify refresh token exists in whitelist"""
        key = f"refresh_token:{token_id}"
        return await self.get(key)
    
    async def revoke_refresh_token(self, token_id: str) -> bool:
        """Revoke a refresh token"""
        key = f"refresh_token:{token_id}"
        return await self.delete(key) > 0
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user"""
        pattern = f"refresh_token:*"
        client = await self._get_client()

        count = 0
        async for key in client.scan_iter(match=pattern):
            token_data = await self.get(key.decode() if isinstance(key, bytes) else key)
            if token_data and token_data.get("user_id") == user_id:
                await self.delete(key)
                count += 1

        return count
    
    async def blacklist_access_token(
        self, token_id: str, expire_seconds: int
    ) -> bool:
        """
        Add access token to blacklist
        Used when user logs out before token expires
        """
        key = f"blacklist:{token_id}"
        return await self.set(key, "1", expire=expire_seconds)
    
    async def is_token_blacklisted(self, token_id: str) -> bool:
        """Check if access token is blacklisted"""
        key = f"blacklist:{token_id}"
        return await self.exists(key) > 0
    
    # ==============================================================================
    # Cache Operations
    # ==============================================================================

    async def cache_set(
        self, key: str, value: Any, expire_minutes: int = 60
    ) -> bool:
        """Set cache with expiration in minutes"""
        return await self.set(key, value, expire=expire_minutes * 60)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return await self.get(key)
    
    async def cache_delete(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        client = await self._get_client()
        count = 0

        async for key in client.scan_iter(match=pattern):
            await self.delete(key)
            count += 1

        return count
    

# Global Redis service instance
redis_service = RedisService()


async def get_redis_service() -> RedisService:
    """Dependency for getting Redis service in FastAPI routes"""
    return redis_service
