"""Cache manager for storing and retrieving API responses to save credits"""
import json
import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of API responses to reduce credit usage"""

    def __init__(self, cache_dir: Path = Path("data/cache"), ttl_hours: int = 168):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory for cache database
            ttl_hours: Time-to-live for cache entries in hours (default: 7 days)
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "response_cache.db"
        self.ttl = timedelta(hours=ttl_hours)

        self._init_database()
        logger.info(f"Cache manager initialized with TTL of {ttl_hours} hours")

    def _init_database(self):
        """Initialize SQLite database for cache storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    response TEXT NOT NULL,
                    probability REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires
                ON response_cache(expires_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_prompt
                ON response_cache(model, prompt_hash)
            """)
            conn.commit()

    def _generate_cache_key(self, model: str, prompt: str) -> str:
        """
        Generate unique cache key for model/prompt combination

        Args:
            model: Model identifier
            prompt: Prompt text

        Returns:
            SHA256 hash as cache key
        """
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_prompt_hash(self, prompt: str) -> str:
        """
        Generate hash of prompt for searching similar prompts

        Args:
            prompt: Prompt text

        Returns:
            SHA256 hash of prompt
        """
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def get(self, model: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if available and not expired

        Args:
            model: Model identifier
            prompt: Prompt text

        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_cache_key(model, prompt)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response, probability, timestamp, created_at
                FROM response_cache
                WHERE cache_key = ? AND expires_at > datetime('now')
            """, (cache_key,))

            result = cursor.fetchone()

            if result:
                response_data = json.loads(result[0])
                # Update with cached metadata
                response_data['probability'] = result[1]
                response_data['timestamp'] = result[2]
                response_data['from_cache'] = True
                response_data['cache_created'] = result[3]

                logger.debug(f"Cache HIT for model {model}")
                return response_data

        logger.debug(f"Cache MISS for model {model}")
        return None

    def set(self, model: str, prompt: str, response: Dict[str, Any]) -> None:
        """
        Store response in cache

        Args:
            model: Model identifier
            prompt: Prompt text
            response: Response data to cache
        """
        cache_key = self._generate_cache_key(model, prompt)
        prompt_hash = self._generate_prompt_hash(prompt)

        now = datetime.now()
        expires_at = now + self.ttl

        # Extract key fields
        probability = response.get('probability')
        timestamp = response.get('timestamp', now.isoformat())

        # Store response
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO response_cache
                (cache_key, model, prompt_hash, response, probability,
                 timestamp, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key,
                model,
                prompt_hash,
                json.dumps(response),
                probability,
                timestamp,
                now.isoformat(),
                expires_at.isoformat()
            ))
            conn.commit()

        logger.debug(f"Cached response for model {model}, expires at {expires_at}")

    def get_similar(self, prompt: str, similarity_threshold: float = 0.95) -> Optional[Dict[str, Any]]:
        """
        Find similar cached prompts (useful for slight variations)

        Args:
            prompt: Prompt text
            similarity_threshold: Minimum similarity score

        Returns:
            Most similar cached response or None
        """
        prompt_hash = self._generate_prompt_hash(prompt)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response, model, created_at
                FROM response_cache
                WHERE prompt_hash = ? AND expires_at > datetime('now')
                ORDER BY created_at DESC
                LIMIT 1
            """, (prompt_hash,))

            result = cursor.fetchone()

            if result:
                response_data = json.loads(result[0])
                response_data['from_cache'] = True
                response_data['similar_match'] = True
                response_data['cached_model'] = result[1]
                response_data['cache_created'] = result[2]
                logger.debug(f"Found similar cached response from {result[1]}")
                return response_data

        return None

    def clear_expired(self) -> int:
        """
        Remove expired cache entries

        Returns:
            Number of entries removed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM response_cache
                WHERE expires_at <= datetime('now')
            """)
            count = cursor.fetchone()[0]

            cursor.execute("""
                DELETE FROM response_cache
                WHERE expires_at <= datetime('now')
            """)
            conn.commit()

            if count > 0:
                logger.info(f"Cleared {count} expired cache entries")

            return count

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total entries
            cursor.execute("SELECT COUNT(*) FROM response_cache")
            total = cursor.fetchone()[0]

            # Active entries
            cursor.execute("""
                SELECT COUNT(*) FROM response_cache
                WHERE expires_at > datetime('now')
            """)
            active = cursor.fetchone()[0]

            # Entries by model
            cursor.execute("""
                SELECT model, COUNT(*)
                FROM response_cache
                WHERE expires_at > datetime('now')
                GROUP BY model
            """)
            by_model = dict(cursor.fetchall())

            # Cache size
            cursor.execute("""
                SELECT SUM(LENGTH(response))
                FROM response_cache
            """)
            size_bytes = cursor.fetchone()[0] or 0

            return {
                'total_entries': total,
                'active_entries': active,
                'expired_entries': total - active,
                'entries_by_model': by_model,
                'cache_size_mb': round(size_bytes / (1024 * 1024), 2),
                'database_path': str(self.db_path)
            }

    def export_for_testing(self, output_file: Path) -> int:
        """
        Export cached responses for offline testing

        Args:
            output_file: Path to export JSON file

        Returns:
            Number of entries exported
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model, prompt_hash, response, probability, timestamp
                FROM response_cache
                WHERE expires_at > datetime('now')
            """)

            results = cursor.fetchall()

            export_data = []
            for row in results:
                export_data.append({
                    'model': row[0],
                    'prompt_hash': row[1],
                    'response': json.loads(row[2]),
                    'probability': row[3],
                    'timestamp': row[4]
                })

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(export_data)} cache entries to {output_file}")
            return len(export_data)