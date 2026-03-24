from contextlib import contextmanager
import os
from typing import List, Dict, Any, Optional

from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

_connection_pool: Optional[ConnectionPool] = None


def initialize_connection_pool(min_size: int = 2, max_size: int = 10):
    global _connection_pool

    if _connection_pool is None:
        connection_string = (
            f"host={os.getenv('POSTGRES_HOST')} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DATABASE')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}"
        )
        _connection_pool = ConnectionPool(
            connection_string,
            min_size=min_size,
            max_size=max_size,
            open=True
        )


def close_connection_pool():
    """Close all connections in the pool."""
    global _connection_pool
    
    if _connection_pool is not None:
        _connection_pool.close()
        _connection_pool = None


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically returns connection to pool after use.
    
    Yields:
        psycopg connection object
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_spots")
    """
    if _connection_pool is None:
        initialize_connection_pool()
    
    with _connection_pool.connection() as conn:
        yield conn


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as list of dictionaries.
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        
    Returns:
        List of dictionaries with column names as keys
        
    Example:
        results = execute_query(
            "SELECT * FROM parking_spots WHERE id = %s",
            (123,)
        )
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            
            return results
