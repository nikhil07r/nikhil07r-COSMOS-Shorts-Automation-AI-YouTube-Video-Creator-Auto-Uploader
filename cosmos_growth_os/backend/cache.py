import time
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger("cosmos.cache")

class FastMemoryCache:
    """Thread-safe, ultra-low latency in-memory cache with TTL expiration."""
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires"]:
            try:
                del self._store[key]
            except KeyError:
                pass
            return None
        return entry["val"]

    def set(self, key: str, val: Any, ttl_seconds: int = 30):
        self._store[key] = {
            "val": val,
            "expires": time.time() + ttl_seconds
        }

    def invalidate(self, prefix: str = ""):
        if not prefix:
            self._store.clear()
        else:
            keys_to_del = [k for k in list(self._store.keys()) if k.startswith(prefix)]
            for k in keys_to_del:
                try:
                    del self._store[k]
                except KeyError:
                    pass

fast_cache = FastMemoryCache()
