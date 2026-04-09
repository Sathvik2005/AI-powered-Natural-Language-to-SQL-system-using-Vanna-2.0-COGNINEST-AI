"""
Utility functions for SQL validation, chart generation, error handling, and caching.
Features:
- SQL validation for security
- Chart generation with Plotly
- Query caching to avoid redundant API calls
- Structured logging for debugging
- Input validation
"""

import re
import time
import json
import hashlib
from typing import Tuple, Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import plotly.express as px
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler


# ============== STRUCTURED LOGGING CONFIGURATION ==============
def setup_structured_logging(log_file: str = "app.log", log_level=logging.INFO):
    """
    Setup structured logging with file and console handlers.
    Logs are written to both file and console with consistent format.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Format with timestamp, level, and message
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # File handler with rotation (max 5MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_structured_logging()
logger.info("=" * 80)
logger.info("Application started")
logger.info("=" * 80)


# ============== INPUT VALIDATION ==============
class InputValidator:
    """Comprehensive input validation for chat requests"""
    
    # Configuration
    MIN_QUESTION_LENGTH = 3
    MAX_QUESTION_LENGTH = 500
    ALLOWED_CHARACTERS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ?,.:;!()[]{}@#$%&-_*"\'-+=/')
    BLOCKED_PATTERNS = [
        r';.*--',  # SQL comments
        r'/\*.*\*/',  # Block comments
        r'\x00',  # Null bytes
    ]
    
    @staticmethod
    def validate(question: str) -> Tuple[bool, Optional[str]]:
        """
        Validate question input.
        Returns (is_valid, error_message)
        """
        if not question:
            return False, "Question cannot be empty"
        
        question = question.strip()
        
        # Check length
        if len(question) < InputValidator.MIN_QUESTION_LENGTH:
            return False, f"Question too short (minimum {InputValidator.MIN_QUESTION_LENGTH} characters)"
        
        if len(question) > InputValidator.MAX_QUESTION_LENGTH:
            return False, f"Question too long (maximum {InputValidator.MAX_QUESTION_LENGTH} characters)"
        
        # Check for blocked patterns
        for pattern in InputValidator.BLOCKED_PATTERNS:
            if re.search(pattern, question, re.IGNORECASE | re.DOTALL):
                return False, f"Question contains suspicious pattern"
        
        # Log validation success
        logger.debug(f"Input validation passed for: {question[:50]}...")
        return True, None


# ============== QUERY CACHING ==============
class QueryCache:
    """LRU cache for query results with TTL (Time To Live)"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached items (oldest removed when exceeded)
            ttl_seconds: Time to live for cached items (default 1 hour)
        """
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
        logger.info(f"QueryCache initialized: max_size={max_size}, ttl={ttl_seconds}s")
    
    @staticmethod
    def _hash_question(question: str) -> str:
        """Generate hash of question for caching key"""
        return hashlib.md5(question.lower().strip().encode()).hexdigest()
    
    def get(self, question: str) -> Optional[Dict]:
        """
        Get cached result if available and not expired.
        Returns None if not found or expired.
        """
        key = self._hash_question(question)
        
        if key not in self.cache:
            self.misses += 1
            logger.debug(f"Cache MISS for question hash: {key}")
            return None
        
        cached_data = self.cache[key]
        
        # Check if expired
        if time.time() > cached_data['expires_at']:
            del self.cache[key]
            self.misses += 1
            logger.debug(f"Cache MISS for question hash: {key} (expired)")
            return None
        
        # Move to end (LRU)
        self.cache.move_to_end(key)
        self.hits += 1
        
        logger.info(f"Cache HIT for question: {question[:40]}... (cache stats: {self.hits} hits, {self.misses} misses)")
        return cached_data['result']
    
    def set(self, question: str, result: Dict) -> None:
        """Cache a query result"""
        key = self._hash_question(question)
        
        # Remove oldest item if cache is full
        if len(self.cache) >= self.max_size:
            removed_key = next(iter(self.cache))
            del self.cache[removed_key]
            logger.debug(f"Cache evicted oldest entry (cache full: {self.max_size})")
        
        self.cache[key] = {
            'result': result,
            'expires_at': time.time() + self.ttl_seconds
        }
        
        logger.debug(f"Cache SET for question hash: {key}")
    
    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }


# Global cache instance
query_cache = QueryCache(max_size=100, ttl_seconds=3600)  # 1 hour TTL


class SQLValidator:
    """Comprehensive SQL validation for security"""
    
    # Dangerous keywords that should be blocked
    BLOCKED_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'EXEC',
        'EXECUTE', 'CREATE', 'GRANT', 'REVOKE', 'SHUTDOWN',
        'xp_', 'sp_', 'PRAGMA', 'VACUUM', 'ANALYZE', 'ATTACH'
    }
    
    # System tables to block
    BLOCKED_TABLES = {
        'sqlite_master', 'sqlite_temp_master', 'sqlite_sequence',
        'sys', 'information_schema', 'pg_catalog'
    }
    
    @staticmethod
    def validate(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive SQL validation.
        Returns (is_valid, error_message)
        """
        if not sql or not sql.strip():
            logger.warning("SQL validation failed: Query is empty")
            return False, "Query is empty"
        
        sql_upper = sql.upper().strip()
        
        logger.debug(f"Validating SQL: {sql[:100]}...")
        
        # Must be SELECT only
        if not sql_upper.startswith('SELECT'):
            logger.warning(f"SQL validation failed: Non-SELECT query attempted")
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in SQLValidator.BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                logger.warning(f"SQL validation failed: Dangerous keyword '{keyword}' detected")
                return False, f"Dangerous keyword '{keyword}' is not allowed"
        
        # Check for system table access
        for table in SQLValidator.BLOCKED_TABLES:
            if table.lower() in sql.lower():
                logger.warning(f"SQL validation failed: System table '{table}' access blocked")
                return False, f"Access to system table '{table}' is not allowed"
        
        # Basic SQL injection check
        injection_patterns = [
            (r"';.*--", "Comment injection pattern"),
            (r"\*\/.*\/\*", "Comment breaking pattern"),
            (r"(\d+\s+or\s+\d+\s*=\s*\d+)", "Boolean-based injection"),
        ]
        
        for pattern, description in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"SQL validation failed: {description} detected")
                return False, f"Suspicious pattern detected: {description}"
        
        logger.info(f"SQL validation passed: Query is safe")
        return True, None


def generate_chart(
    columns: List[str],
    rows: List[List[Any]],
    question: str = ""
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Generate Plotly chart from query results intelligently.
    Detects data types and creates appropriate visualizations.
    Returns (chart_dict, chart_type) or (None, None)
    """
    try:
        if not rows or not columns or len(columns) < 1:
            logger.debug("Chart generation skipped: No rows or columns")
            return None, None
        
        logger.info(f"Generating chart for {len(rows)} rows, {len(columns)} columns")
        df = pd.DataFrame(rows, columns=columns)
        
        # Need at least 2 columns for meaningful chart
        if df.shape[1] < 2:
            logger.debug("Chart generation skipped: Less than 2 columns")
            return None, None
        
        # Identify numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        logger.debug(f"Identified {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, {len(datetime_cols)} datetime columns")
        
        # Need at least 1 numeric column to visualize
        if not numeric_cols:
            logger.debug("Chart generation skipped: No numeric columns")
            return None, None
        
        # Use first categorical/datetime as X, first numeric as Y
        x_col = categorical_cols[0] if categorical_cols else (datetime_cols[0] if datetime_cols else columns[0])
        y_col = numeric_cols[0]
        
        # Limit rows for visualization
        df_viz = df.head(20)
        
        logger.info(f"Chart columns: X={x_col}, Y={y_col}")
        
        # Determine chart type based on question keywords and data
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['trend', 'over time', 'month', 'by month', 'by year']):
            fig = px.line(df_viz, x=x_col, y=y_col, title=f"Query Result: {question[:50]}", markers=True)
            chart_type = "line"
            logger.info("Chart type: LINE (trend detected)")
        elif any(word in question_lower for word in ['compare', 'by', 'breakdown', 'distribution']):
            # For bar chart, sort by Y to make comparison clearer
            if len(df_viz) > 1:
                df_viz = df_viz.sort_values(y_col, ascending=False)
            fig = px.bar(df_viz, x=x_col, y=y_col, title=f"Query Result: {question[:50]}")
            chart_type = "bar"
            logger.info("Chart type: BAR (comparison detected)")
        elif len(numeric_cols) >= 2 and len(df_viz) > 5:
            fig = px.scatter(df_viz, x=numeric_cols[0], y=numeric_cols[1], 
                           title=f"Query Result: {question[:50]}", 
                           size=numeric_cols[0] if len(numeric_cols) >= 2 else None)
            chart_type = "scatter"
            logger.info("Chart type: SCATTER (multiple numeric detected)")
        else:
            fig = px.bar(df_viz, x=x_col, y=y_col, title=f"Query Result: {question[:50]}")
            chart_type = "bar"
            logger.info("Chart type: BAR (default)")
        
        chart_dict = fig.to_dict()
        logger.info(f"Chart generated successfully: type={chart_type}")
        return chart_dict, chart_type
        
    except Exception as e:
        logger.warning(f"Chart generation failed: {str(e)}", exc_info=True)
        return None, None


def format_response(
    message: str,
    sql_query: str,
    columns: List[str],
    rows: List[List[Any]],
    question: str = ""
) -> Dict[str, Any]:
    """
    Format API response with all required fields.
    Includes automatic chart generation and structured response.
    """
    logger.info(f"Formatting response: {len(rows)} rows, {len(columns)} columns")
    
    chart, chart_type = generate_chart(columns, rows, question)
    
    response = {
        "message": message,
        "sql_query": sql_query,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows) if rows else 0,
        "chart": chart,
        "chart_type": chart_type,
        "error": None
    }
    
    logger.debug(f"Response formatted with chart_type={chart_type}")
    return response


def extract_summary(rows: List[List[Any]], columns: List[str], sql_query: str = "") -> str:
    """
    Generate intelligent summary of query results.
    Analyzes data to provide meaningful insights.
    """
    if not rows:
        logger.debug("Summary: No rows found")
        return "No data matching the query found."
    
    row_count = len(rows)
    
    if row_count == 1:
        summary = f"Found 1 result."
    elif row_count < 10:
        summary = f"Found {row_count} results."
    else:
        summary = f"Found {row_count} results."
    
    # Add column-based insights if possible
    if columns and rows and len(columns) > 0:
        logger.debug(f"Extracting summary insights from {len(columns)} columns")
        # Try to find numeric columns for summary stats
        try:
            numeric_values = []
            for row in rows:
                for value in row:
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_values.append(value)
            
            if numeric_values:
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                avg_val = sum(numeric_values) / len(numeric_values)
                summary += f" Min: {min_val}, Max: {max_val}, Avg: {avg_val:.2f}"
                logger.debug(f"Added numeric statistics to summary")
        except Exception as e:
            logger.debug(f"Could not extract numeric statistics: {str(e)}")
    
    return summary


def log_query(question: str, sql: str, status: str, row_count: int = 0):
    """
    Log query execution with all details for audit trail.
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': question[:100],
        'sql_length': len(sql),
        'status': status,
        'row_count': row_count
    }
    logger.info(f"Query executed: {json.dumps(log_entry)}")


def get_cache_stats() -> Dict[str, Any]:
    """Get query cache statistics"""
    return query_cache.stats()
