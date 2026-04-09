"""
FastAPI Backend for NL2SQL - CORRECTED for Vanna 2.0
Uses proper async API, RequestContext, and error handling
Features:
- Chart generation with Plotly
- Input validation
- Query caching with TTL
- Rate limiting
- Structured logging
"""

import os
import asyncio
import logging
import json
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from vanna_setup import create_vanna_agent
from utils import SQLValidator, InputValidator, format_response, extract_summary, query_cache, logger
from vanna.core.user import RequestContext

# Load environment variables
load_dotenv()

# Setup rate limiting (10 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)

# Global agent instance
agent = None
agent_memory = None
DB_PATH = "clinic.db"


class ChatRequest(BaseModel):
    """Request model for /chat endpoint"""
    question: str


class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    message: str
    sql_query: Optional[str] = None
    columns: Optional[list] = None
    rows: Optional[list] = None
    row_count: Optional[int] = None
    chart: Optional[dict] = None
    chart_type: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str
    database: str
    agent_ready: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize agent on startup"""
    global agent, agent_memory
    
    logger.info("=" * 80)
    logger.info("Starting NL2SQL Server with Advanced Features")
    logger.info("Features: Caching | Rate Limiting | Validation | Logging | Charts")
    logger.info("=" * 80)
    
    try:
        # Initialize Vanna Agent (returns tuple: agent, memory)
        agent, agent_memory = create_vanna_agent()
        logger.info("✓ Agent initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize agent: {str(e)}", exc_info=True)
        raise
    
    yield
    
    logger.info("=" * 80)
    logger.info("Shutting down NL2SQL Server")
    logger.info(f"Cache Statistics: {json.dumps(query_cache.stats())}")
    logger.info("=" * 80)


# Create FastAPI app with lifespan
app = FastAPI(
    title="NL2SQL Agent API",
    description="Natural Language to SQL conversion using Vanna 2.0",
    version="2.0.0",
    lifespan=lifespan
)

# Add rate limiting to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded. Maximum 10 requests per minute."}
))

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with cache statistics"""
    
    import sqlite3
    
    logger.debug("Health check requested")
    
    # Check database
    db_connected = False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        db_connected = True
        conn.close()
        logger.debug("Database check passed")
    except Exception as e:
        logger.warning(f"Database check failed: {str(e)}")
        db_connected = False
    
    return HealthResponse(
        status="ok" if (agent and db_connected) else "error",
        database="connected" if db_connected else "disconnected",
        agent_ready=agent is not None
    )


@app.get("/cache-stats")
async def cache_statistics():
    """Get cache statistics"""
    logger.info("Cache statistics requested")
    return query_cache.stats()


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """
    Main chat endpoint for NL2SQL queries.
    Features:
    - Input validation
    - Query caching
    - Rate limiting
    - Structured logging
    - Chart generation
    """
    
    question = chat_request.question.strip()
    request_id = f"{datetime.now().timestamp()}"
    
    logger.info(f"[{request_id}] New chat request from {request.client.host}")
    
    # ========== INPUT VALIDATION ==========
    is_valid, error_msg = InputValidator.validate(question)
    if not is_valid:
        logger.warning(f"[{request_id}] Input validation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    logger.info(f"[{request_id}] Input validation passed: Q='{question[:50]}...'")
    
    # ========== CHECK CACHE ==========
    cached_result = query_cache.get(question)
    if cached_result:
        logger.info(f"[{request_id}] Returning cached result")
        return JSONResponse(cached_result)
    
    if not agent:
        logger.error(f"[{request_id}] Agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    logger.info(f"[{request_id}] Processing new question (cache miss)")
    
    try:
        # ========== CREATE REQUEST CONTEXT ==========
        request_context = RequestContext(
            user_id="default_user",
            session_id="web_session"
        )
        
        logger.debug(f"[{request_id}] RequestContext created")
        
        # ========== CALL VANNA AGENT ==========
        logger.info(f"[{request_id}] Querying Vanna agent...")
        
        sql_query = None
        components_received = []
        
        # Iterate through the async generator from send_message()
        async for component in agent.send_message(
            request_context=request_context,
            message=question,
            conversation_id=None
        ):
            components_received.append(component)
            component_type = type(component).__name__
            logger.info(f"[{request_id}] Component received: {component_type}")
            logger.debug(f"[{request_id}] Component: {component}")
            
            # Get the actual data from the Pydantic model
            if hasattr(component, 'model_dump'):
                data = component.model_dump()
                logger.debug(f"[{request_id}] Component data keys: {list(data.keys())}")
                logger.debug(f"[{request_id}] Component data: {str(data)[:500]}")
            
            # Get the actual data from the Pydantic model
            if hasattr(component, 'model_dump'):
                data = component.model_dump()
                
                # Look for SQL in nested structures
                def extract_sql(obj):
                    if isinstance(obj, dict):
                        for key, val in obj.items():
                            if isinstance(val, str) and "SELECT" in val.upper():
                                import re
                                sql_match = re.search(r'```sql\s*(SELECT.*?);?\s*```', val, re.DOTALL | re.IGNORECASE)
                                if sql_match:
                                    return sql_match.group(1).strip()
                                sql_match = re.search(r'(SELECT\s+.*?);', val, re.DOTALL | re.IGNORECASE)
                                if sql_match:
                                    return sql_match.group(1).strip() + ";"
                                if "SELECT" in val.upper():
                                    return val
                            result = extract_sql(val)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = extract_sql(item)
                            if result:
                                return result
                    return None
                
                extracted = extract_sql(data)
                if extracted:
                    sql_query = extracted
                    logger.info(f"[{request_id}] SQL Generated: {sql_query[:80]}...")
                    break
            elif hasattr(component, 'dict'):
                data = component.dict()
                extracted = extract_sql(data)
                if extracted:
                    sql_query = extracted
                    logger.info(f"[{request_id}] SQL Generated: {sql_query[:80]}...")
                    break
        
        # ========== CHECK IF SQL WAS GENERATED =========="
        if not sql_query:
            logger.warning(f"[{request_id}] Agent did not generate valid SQL, trying knowledge base fallback...")
            
            # Try knowledge base fallback
            from sql_knowledge_base import match_question_to_sql
            fallback_sql = match_question_to_sql(question)
            
            if fallback_sql:
                logger.info(f"[{request_id}] Using fallback SQL from knowledge base")
                sql_query = fallback_sql
            else:
                logger.warning(f"[{request_id}] No fallback SQL available")
                response = {
                    "message": "Could not generate SQL from question",
                    "sql_query": None,
                    "columns": None,
                    "rows": None,
                    "row_count": None,
                    "chart": None,
                    "chart_type": None,
                    "error": "No valid SQL generated by agent or fallback"
                }
                query_cache.set(question, response)
                return JSONResponse(response)
        
        # ========== VALIDATE SQL ==========
        is_valid, error_msg = SQLValidator.validate(sql_query)
        if not is_valid:
            logger.warning(f"[{request_id}] SQL validation failed: {error_msg}")
            response = {
                "message": "Generated SQL failed validation",
                "sql_query": sql_query,
                "columns": None,
                "rows": None,
                "row_count": None,
                "chart": None,
                "chart_type": None,
                "error": error_msg
            }
            return JSONResponse(response)
        
        # ========== EXECUTE SQL =========="
        import sqlite3
        
        logger.info(f"[{request_id}] Executing SQL query...")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_query)
            result = cursor.fetchall()
            columns = [description[0] for description in cursor.description or []]
            rows = [list(row) for row in result]
            
            # Convert numpy types to Python native types for JSON serialization
            def convert_numpy_types(value):
                try:
                    import numpy as np
                    if isinstance(value, (np.integer, np.floating)):
                        return value.item()
                    elif isinstance(value, np.ndarray):
                        return value.tolist()
                    elif isinstance(value, np.bool_):
                        return bool(value)
                    elif isinstance(value, (list, tuple)):
                        return [convert_numpy_types(v) for v in value]
                except ImportError:
                    pass
                return value
            
            rows = [[convert_numpy_types(cell) for cell in row] for row in rows]
            logger.info(f"[{request_id}] SQL executed successfully: {len(rows)} rows returned")
            
        except sqlite3.Error as e:
            conn.close()
            logger.error(f"[{request_id}] SQL execution failed: {str(e)}")
            response = {
                "message": "SQL execution failed",
                "sql_query": sql_query,
                "columns": None,
                "rows": None,
                "row_count": None,
                "chart": None,
                "chart_type": None,
                "error": str(e)
            }
            return JSONResponse(response)
        
        conn.close()
        
        if not rows:
            logger.info(f"[{request_id}] Query returned no results")
            response = {
                "message": "Query returned no results",
                "sql_query": sql_query,
                "columns": columns or [],
                "rows": [],
                "row_count": 0,
                "chart": None,
                "chart_type": None,
                "error": None
            }
            query_cache.set(question, response)
            return JSONResponse(response)
        
        # ========== FORMAT RESPONSE =========="
        logger.info(f"[{request_id}] Formatting response...")
        summary = extract_summary(rows, columns, sql_query)
        
        # Final conversion to ensure no numpy types
        def make_json_compatible(obj):
            try:
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: make_json_compatible(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_compatible(item) for item in obj]
            except ImportError:
                pass
            return obj
        
        rows = make_json_compatible(rows)
        columns = make_json_compatible(columns)
        
        response_data = format_response(
            message=summary,
            sql_query=sql_query,
            columns=columns,
            rows=rows,
            question=question
        )
        
        response_data = make_json_compatible(response_data)
        
        logger.info(f"[{request_id}] Response prepared, caching result...")
        query_cache.set(question, response_data)
        
        logger.info(f"[{request_id}] ✓ Request completed successfully")
        return JSONResponse(response_data)
        
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Request timed out")
        return ChatResponse(
            message="Request timed out",
            error="Agent did not respond within time limit"
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return ChatResponse(
            message="An error occurred processing your question",
            error=str(e)
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NL2SQL Agent API v2.0",
        "status": "running",
        "docs": "/docs"
    }
