"""
Base API Client for RetailMate
Provides common functionality for all API integrations
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import httpx
from cachetools import TTLCache
from pydantic import BaseModel, Field

logger = logging.getLogger("retailmate-api")

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until we can make another call
            wait_time = 60 - (now - self.calls[0]).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
        
        self.calls.append(now)

class BaseAPIClient:
    """Base class for all API clients"""
    
    def __init__(self, base_url: str, name: str, rate_limit: int = 60):
        self.base_url = base_url.rstrip('/')
        self.name = name
        self.rate_limiter = RateLimiter(rate_limit)
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
        self.session: Optional[httpx.AsyncClient] = None
        
        logger.info(f"Initialized {self.name} API client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "RetailMate/1.0",
                "Accept": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and caching"""
        # Check cache first for GET requests
        cache_key = f"{method}:{endpoint}:{str(kwargs)}"
        if method.upper() == "GET" and cache_key in self.cache:
            logger.debug(f"Cache hit for {self.name}: {endpoint}")
            return self.cache[cache_key]
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making {method} request to {url}")
        
        try:
            if not self.session:
                raise APIError("Session not initialized. Use async context manager.")
            
            response = await self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache successful GET requests
            if method.upper() == "GET":
                self.cache[cache_key] = data
            
            return data
            
        except httpx.HTTPStatusError as e:
            error_msg = f"{self.name} API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
            
            raise APIError(error_msg, e.response.status_code, getattr(e.response, 'json', lambda: {})())
        
        except httpx.RequestError as e:
            raise APIError(f"{self.name} request error: {str(e)}")
        
        except Exception as e:
            raise APIError(f"{self.name} unexpected error: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, data=data, json=json)
    
    def clear_cache(self):
        """Clear the request cache"""
        self.cache.clear()
        logger.info(f"Cleared cache for {self.name}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hits": getattr(self.cache, 'hits', 0),
            "misses": getattr(self.cache, 'misses', 0)
        }
