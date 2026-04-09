"""
Utility functions for SQL validation, chart generation, and error handling
"""

import re
from typing import Tuple, Optional, List, Dict, Any
import plotly.express as px
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries for safety"""
    
    # Dangerous keywords that should be blocked
    BLOCKED_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'EXEC',
        'EXECUTE', 'CREATE', 'GRANT', 'REVOKE', 'SHUTDOWN',
        'xp_', 'sp_'
    }
    
    # System tables to block
    BLOCKED_TABLES = {
        'sqlite_master', 'sqlite_temp_master', 'sqlite_sequence',
        'sys', 'information_schema'
    }
    
    @staticmethod
    def validate(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query.
        Returns (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Query is empty"
        
        sql_upper = sql.upper().strip()
        
        # Must be SELECT only
        if not sql_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in SQLValidator.BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Dangerous keyword '{keyword}' is not allowed"
        
        # Check for system table access
        for table in SQLValidator.BLOCKED_TABLES:
            if table.lower() in sql.lower():
                return False, f"Access to system table '{table}' is not allowed"
        
        # Basic SQL injection check
        suspicious_patterns = [
            r"';.*--",  # Comment injection
            r"\*\/.*\/\*",  # Comment breaking
            r"(UNION|EXCEPT|INTERSECT)",  # Multi-result tricks
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                # Note: UNION is allowed but logged
                if pattern == r"(UNION|EXCEPT|INTERSECT)":
                    logger.warning(f"Query uses advanced SQL: {pattern}")
                    continue
                return False, f"Suspicious pattern detected: {pattern}"
        
        return True, None


def generate_chart(
    columns: List[str],
    rows: List[List[Any]],
    question: str = ""
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Generate Plotly chart from query results.
    Returns (chart_dict, chart_type) or (None, None)
    """
    try:
        if not rows or not columns or len(columns) < 1:
            return None, None
        
        df = pd.DataFrame(rows, columns=columns)
        
        # Need at least 2 columns for meaningful chart
        if df.shape[1] < 2:
            return None, None
        
        # Identify numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if not numeric_cols or not categorical_cols:
            return None, None
        
        # Use first categorical as X, first numeric as Y
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        # Limit rows for visualization
        df_viz = df.head(20)
        
        # Determine chart type based on question keywords
        if any(word in question.lower() for word in ['trend', 'month', 'time']):
            fig = px.line(df_viz, x=x_col, y=y_col, title=question)
            chart_type = "line"
        elif any(word in question.lower() for word in ['compare', 'by']):
            fig = px.bar(df_viz, x=x_col, y=y_col, title=question)
            chart_type = "bar"
        elif len(numeric_cols) >= 2:
            fig = px.scatter(df_viz, x=x_col, y=y_col, title=question)
            chart_type = "scatter"
        else:
            fig = px.bar(df_viz, x=x_col, y=y_col, title=question)
            chart_type = "bar"
        
        return fig.to_dict(), chart_type
        
    except Exception as e:
        logger.warning(f"Chart generation failed: {str(e)}")
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
    Includes automatic chart generation.
    """
    chart, chart_type = generate_chart(columns, rows, question)
    
    return {
        "message": message,
        "sql_query": sql_query,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows) if rows else 0,
        "chart": chart,
        "chart_type": chart_type
    }


def extract_summary(rows: List[List[Any]], columns: List[str]) -> str:
    """Generate a friendly summary of query results"""
    if not rows:
        return "No data found."
    
    if len(rows) == 1:
        return f"Found 1 result."
    
    return f"Found {len(rows)} results."


def log_query(question: str, sql: str, status: str):
    """Log query execution for debugging"""
    logger.info(f"Q: {question}")
    logger.info(f"SQL: {sql}")
    logger.info(f"Status: {status}")
