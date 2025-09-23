"""
Neon PostgreSQL Database Connection and Operations
"""
import os
import asyncpg
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from contextlib import asynccontextmanager

# Database connection pool
_pool = None

async def init_db():
    """Initialize database connection pool"""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Parse connection string for asyncpg
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    return _pool

async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

@asynccontextmanager
async def get_db():
    """Get database connection from pool"""
    pool = await init_db()
    async with pool.acquire() as connection:
        yield connection

async def save_forecast(forecast_data: Dict[str, Any]) -> str:
    """Save a new forecast to the database"""
    async with get_db() as conn:
        query = """
            INSERT INTO forecasts (
                id, user_id, question, definition, timeframe,
                forecast_type, status, created_at, total_queries
            ) VALUES (
                $1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9
            ) RETURNING id
        """

        forecast_id = await conn.fetchval(
            query,
            forecast_data.get("id"),
            forecast_data.get("user_id"),
            forecast_data.get("question"),
            forecast_data.get("definition"),
            forecast_data.get("timeframe"),
            forecast_data.get("forecast_type", "custom"),
            forecast_data.get("status", "pending"),
            forecast_data.get("created_at", datetime.now()),
            forecast_data.get("total_queries", 0)
        )

        return str(forecast_id)

async def update_forecast_status(
    forecast_id: str,
    status: str,
    ensemble_probability: Optional[float] = None,
    excel_url: Optional[str] = None,
    error: Optional[str] = None
):
    """Update forecast status and results"""
    async with get_db() as conn:
        # Build update query dynamically
        updates = ["status = $2"]
        params = [forecast_id, status]
        param_count = 2

        if ensemble_probability is not None:
            param_count += 1
            updates.append(f"ensemble_probability = ${param_count}")
            params.append(ensemble_probability)

        if excel_url is not None:
            param_count += 1
            updates.append(f"excel_url = ${param_count}")
            params.append(excel_url)

        if status == "running":
            param_count += 1
            updates.append(f"started_at = ${param_count}")
            params.append(datetime.now())
        elif status in ["completed", "error", "cancelled"]:
            param_count += 1
            updates.append(f"completed_at = ${param_count}")
            params.append(datetime.now())

        if error:
            param_count += 1
            updates.append(f"metadata = metadata || ${param_count}::jsonb")
            params.append(json.dumps({"error": error}))

        query = f"""
            UPDATE forecasts
            SET {', '.join(updates)}
            WHERE id = $1::uuid
        """

        await conn.execute(query, *params)

async def save_model_response(response_data: Dict[str, Any]):
    """Save a model response to the database"""
    async with get_db() as conn:
        query = """
            INSERT INTO model_responses (
                forecast_id, model, iteration, ensemble_id, status,
                probability, content, response_time, token_usage, error_message
            ) VALUES (
                $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10
            )
        """

        token_usage = None
        if response_data.get("token_usage"):
            token_usage = json.dumps(response_data["token_usage"])

        await conn.execute(
            query,
            response_data.get("forecast_id"),
            response_data.get("model"),
            response_data.get("iteration"),
            response_data.get("ensemble_id"),
            response_data.get("status"),
            response_data.get("probability"),
            response_data.get("content"),
            response_data.get("response_time"),
            token_usage,
            response_data.get("error_message")
        )

async def save_forecast_statistics(forecast_id: str, statistics: Dict[str, Any]):
    """Save forecast statistics to the database"""
    async with get_db() as conn:
        query = """
            INSERT INTO forecast_statistics (
                forecast_id, mean_probability, median_probability,
                std_deviation, min_probability, max_probability,
                confidence_interval_lower, confidence_interval_upper,
                model_stats, consensus_strength
            ) VALUES (
                $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10
            )
            ON CONFLICT (forecast_id) DO UPDATE SET
                mean_probability = $2,
                median_probability = $3,
                std_deviation = $4,
                min_probability = $5,
                max_probability = $6,
                confidence_interval_lower = $7,
                confidence_interval_upper = $8,
                model_stats = $9::jsonb,
                consensus_strength = $10
        """

        await conn.execute(
            query,
            forecast_id,
            statistics.get("mean"),
            statistics.get("median"),
            statistics.get("std"),
            statistics.get("min"),
            statistics.get("max"),
            statistics.get("ci_lower"),
            statistics.get("ci_upper"),
            json.dumps(statistics.get("model_stats", {})),
            statistics.get("consensus_strength")
        )

async def get_forecast(forecast_id: str) -> Optional[Dict[str, Any]]:
    """Get forecast details from database"""
    async with get_db() as conn:
        query = """
            SELECT
                id, user_id, question, definition, timeframe,
                forecast_type, status, ensemble_probability,
                created_at, started_at, completed_at,
                excel_url, total_queries, successful_queries,
                failed_queries, metadata
            FROM forecasts
            WHERE id = $1::uuid
        """

        row = await conn.fetchrow(query, forecast_id)
        if row:
            return dict(row)
        return None

async def get_forecast_responses(forecast_id: str) -> List[Dict[str, Any]]:
    """Get all model responses for a forecast"""
    async with get_db() as conn:
        query = """
            SELECT
                id, model, iteration, ensemble_id, status,
                probability, content, response_time, token_usage,
                error_message, created_at
            FROM model_responses
            WHERE forecast_id = $1::uuid
            ORDER BY created_at ASC
        """

        rows = await conn.fetch(query, forecast_id)
        return [dict(row) for row in rows]

async def list_forecasts(
    user_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """List forecasts with optional filtering"""
    async with get_db() as conn:
        where_clause = ""
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            where_clause = f"WHERE user_id = ${param_count}::uuid"
            params.append(user_id)

        # Count total
        count_query = f"""
            SELECT COUNT(*) FROM forecasts {where_clause}
        """
        total = await conn.fetchval(count_query, *params)

        # Fetch forecasts
        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(offset)

        list_query = f"""
            SELECT
                id, question, definition, timeframe, status,
                ensemble_probability, created_at, completed_at
            FROM forecasts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """

        rows = await conn.fetch(list_query, *params)

        return {
            "forecasts": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset
        }

async def create_forecast_share(forecast_id: str, expires_in_hours: int = 24) -> str:
    """Create a shareable link for a forecast"""
    import uuid
    from datetime import timedelta

    async with get_db() as conn:
        share_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        query = """
            INSERT INTO forecast_shares (
                forecast_id, share_token, expires_at
            ) VALUES (
                $1::uuid, $2, $3
            ) RETURNING share_token
        """

        token = await conn.fetchval(query, forecast_id, share_token, expires_at)
        return token

async def get_forecast_by_share_token(share_token: str) -> Optional[Dict[str, Any]]:
    """Get forecast by share token"""
    async with get_db() as conn:
        # Check if token is valid and not expired
        query = """
            SELECT f.*, fs.expires_at
            FROM forecast_shares fs
            JOIN forecasts f ON fs.forecast_id = f.id
            WHERE fs.share_token = $1
            AND (fs.expires_at IS NULL OR fs.expires_at > NOW())
        """

        row = await conn.fetchrow(query, share_token)
        if row:
            # Update access count
            await conn.execute(
                "UPDATE forecast_shares SET access_count = access_count + 1 WHERE share_token = $1",
                share_token
            )
            return dict(row)
        return None