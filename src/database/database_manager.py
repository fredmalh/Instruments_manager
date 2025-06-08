import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator, Callable
import queue
import threading
from pathlib import Path
import logging
import time
import uuid
from .config import DatabaseConfig

class DatabaseError(Exception):
    """Base exception for database-related errors"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Raised when there are issues with database connections"""
    pass

class DatabaseQueryError(DatabaseError):
    """Raised when there are issues with database queries"""
    pass

class DatabaseLockError(DatabaseError):
    """Exception raised for database locking errors"""
    pass

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _connection_pool = []
    _max_pool_size = 5
    _timeout = 5
    _pool_lock = threading.Lock()
    _transaction_lock = threading.Lock()
    _active_transactions = set()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = None, pool_size: int = None):
        if not hasattr(self, 'initialized'):
            self.db_path = db_path or DatabaseConfig.get_database_path()
            self._max_pool_size = pool_size or DatabaseConfig.get_settings()['pool_size']
            self._timeout = DatabaseConfig.get_settings()['timeout']
            self.initialized = True
            self._initialize_pool()
            
            # Configure logging
            self.logger = logging.getLogger(__name__)
            
    def _initialize_pool(self) -> None:
        """Initialize the connection pool with the specified number of connections"""
        try:
            for _ in range(self._max_pool_size):
                conn = self._create_connection()
                self._connection_pool.append(conn)
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize connection pool: {str(e)}")
            
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with proper configuration"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self._timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to create database connection: {str(e)}")
            
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool"""
        with self._pool_lock:
            if not self._connection_pool:
                # If pool is empty, create a new connection
                return self._create_connection()
            return self._connection_pool.pop()

    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        with self._pool_lock:
            if len(self._connection_pool) < self._max_pool_size:
                self._connection_pool.append(conn)
            else:
                conn.close()

    def _acquire_transaction_lock(self, transaction_id: str, timeout: int = 5) -> bool:
        """Acquire a lock for a transaction"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._transaction_lock:
                if transaction_id not in self._active_transactions:
                    self._active_transactions.add(transaction_id)
                    return True
            time.sleep(0.1)
        return False

    def _release_transaction_lock(self, transaction_id: str):
        """Release a transaction lock"""
        with self._transaction_lock:
            self._active_transactions.discard(transaction_id)

    @contextmanager
    def transaction(self, transaction_id: str = None):
        """Context manager for database transactions with locking"""
        if transaction_id is None:
            transaction_id = str(uuid.uuid4())
            
        if not self._acquire_transaction_lock(transaction_id):
            raise DatabaseLockError("Failed to acquire transaction lock")
            
        conn = None
        try:
            conn = self._get_connection()
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseQueryError(f"Transaction failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)
            self._release_transaction_lock(transaction_id)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return the results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries containing the query results
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseQueryError(f"Query execution failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an UPDATE, INSERT, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Update execution failed: {str(e)}")
            raise DatabaseQueryError(f"Update execution failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute multiple INSERT or UPDATE operations in a single transaction.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Batch execution failed: {str(e)}")
            raise DatabaseQueryError(f"Batch execution failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)

    def get_single_row(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return a single row.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Dictionary containing the row data or None if no row found
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseQueryError(f"Query execution failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)

    def get_scalar(self, query: str, params: tuple = ()) -> Any:
        """
        Execute a query and return a single value.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            The scalar value or None if no value found
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseQueryError(f"Query execution failed: {str(e)}")
        finally:
            if conn:
                self._return_connection(conn)

    def execute_in_transaction(self, transaction_id: str, operations: List[Callable]):
        """Execute multiple operations in a single transaction with locking"""
        with self.transaction(transaction_id) as conn:
            for operation in operations:
                operation(conn)

    def close(self) -> None:
        """Close all connections in the pool"""
        with self._pool_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Error closing connection: {str(e)}") 