"""
FastAPI Backend for NL2SQL - CORRECTED for Vanna 2.0
Uses proper async API, RequestContext, and error handling
"""

import os
import asyncio
import logging
import json
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from vanna_setup import create_vanna_agent
from utils import SQLValidator, format_response, extract_summary
from vanna.core.user import RequestContext

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    print("\n[*] Starting NL2SQL Server...\n")
    
    try:
        # Initialize Vanna Agent (returns tuple: agent, memory)
        agent, agent_memory = create_vanna_agent()
        print("[+] Agent initialized successfully\n")
    except Exception as e:
        logger.error(f"[-] Failed to initialize agent: {str(e)}")
        print(f"[-] Failed to initialize agent: {str(e)}")
        raise
    
    yield
    
    print("\n[*] Shutting down NL2SQL Server...\n")


# Create FastAPI app with lifespan
app = FastAPI(
    title="NL2SQL Agent API",
    description="Natural Language to SQL conversion using Vanna 2.0",
    version="2.0.0",
    lifespan=lifespan
)

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
    """Health check endpoint"""
    
    import sqlite3
    
    # Check database
    db_connected = False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        db_connected = True
        conn.close()
    except Exception as e:
        logger.warning(f"Database check failed: {str(e)}")
        db_connected = False
    
    return HealthResponse(
        status="ok" if (agent and db_connected) else "error",
        database="connected" if db_connected else "disconnected",
        agent_ready=agent is not None
    )


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint for NL2SQL queries.
    Properly uses Vanna 2.0 async API with RequestContext.
    """
    
    question = request.question.strip()
    
    # Validate input
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 chars)")
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    logger.info(f"[*] Received question: {question}")
    
    try:
        # ========== CREATE REQUEST CONTEXT ==========
        # This is REQUIRED for Vanna 2.0 send_message()
        request_context = RequestContext(
            user_id="default_user",
            session_id="web_session"
        )
        
        # ========== CALL VANNA AGENT ==========
        # send_message() is async generator yielding UI Components
        logger.info(f"[*] Querying agent...")
        
        sql_query = None
        components_received = []
        
        # Iterate through the async generator from send_message()
        async for component in agent.send_message(
            request_context=request_context,
            message=question,
            conversation_id=None
        ):
            components_received.append(component)
            logger.info(f"[COMPONENT] {len(components_received)}: {type(component).__name__}")
            
            # Get the actual data from the Pydantic model
            if hasattr(component, 'model_dump'):
                data = component.model_dump()
                
                # Look for SQL in nested structures (especially text content)
                def extract_sql(obj):
                    if isinstance(obj, dict):
                        for key, val in obj.items():
                            # Check if this field contains SQL
                            if isinstance(val, str) and "SELECT" in val.upper():
                                # Extract SQL from markdown code blocks or plain text
                                import re
                                # First try to extract from ```sql ... ``` blocks
                                sql_match = re.search(r'```sql\s*(SELECT.*?);?\s*```', val, re.DOTALL | re.IGNORECASE)
                                if sql_match:
                                    return sql_match.group(1).strip()
                                # Otherwise try to find SELECT statement
                                sql_match = re.search(r'(SELECT\s+.*?);', val, re.DOTALL | re.IGNORECASE)
                                if sql_match:
                                    return sql_match.group(1).strip() + ";"
                                # Fallback: return whole value if it contains SELECT
                                if "SELECT" in val.upper():
                                    return val
                            # Recursively check nested structures
                            result = extract_sql(val)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = extract_sql(item)
                            if result:
                                return result
                    return None
                
                # Try to extract SQL from the component data
                extracted = extract_sql(data)
                if extracted:
                    sql_query = extracted
                    logger.info(f"[+] Found SQL: {sql_query[:100]}")
                    break
            elif hasattr(component, 'dict'):
                # Fallback for older Pydantic versions
                data = component.dict()
                extracted = extract_sql(data)
                if extracted:
                    sql_query = extracted
                    logger.info(f"[+] Found SQL: {sql_query[:100]}")
                    break
        
        # ========== CHECK IF SQL WAS GENERATED =========="
        if not sql_query:
            logger.warning("[-] Agent did not generate valid SQL")
            return JSONResponse({
                "message": "Could not generate SQL from question",
                "sql_query": None,
                "columns": None,
                "rows": None,
                "row_count": None,
                "chart": None,
                "chart_type": None,
                "error": "No valid SQL generated by agent"
            })
        
        # ========== VALIDATE SQL ==========
        is_valid, error_msg = SQLValidator.validate(sql_query)
        if not is_valid:
            logger.warning(f"[-] SQL validation failed: {error_msg}")
            return JSONResponse({
                "message": "Generated SQL failed validation",
                "sql_query": sql_query,
                "columns": None,
                "rows": None,
                "row_count": None,
                "chart": None,
                "chart_type": None,
                "error": error_msg
            })
        
        # ========== EXECUTE SQL =========="
        import sqlite3
        
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
            
        except sqlite3.Error as e:
            conn.close()
            logger.error(f"[-] SQL execution failed: {str(e)}")
            return JSONResponse({
                "message": "SQL execution failed",
                "sql_query": sql_query,
                "columns": None,
                "rows": None,
                "row_count": None,
                "chart": None,
                "chart_type": None,
                "error": str(e)
            })
        
        conn.close()
        
        logger.info(f"[+] Query successful: {len(rows)} rows")
        
        if not rows:
            return JSONResponse({
                "message": "Query returned no results",
                "sql_query": sql_query,
                "columns": columns or [],
                "rows": [],
                "row_count": 0,
                "chart": None,
                "chart_type": None,
                "error": None
            })
        
        # ========== FORMAT RESPONSE =========="
        summary = extract_summary(rows, columns)
        
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
        
        # Convert all data to JSON-compatible types
        rows = make_json_compatible(rows)
        columns = make_json_compatible(columns)
        
        response_data = format_response(
            message=summary,
            sql_query=sql_query,
            columns=columns,
            rows=rows,
            question=question
        )
        
        # Convert response data to JSON-compatible format
        response_data = make_json_compatible(response_data)
        
        return JSONResponse(response_data)
        
    except asyncio.TimeoutError:
        logger.error("[-] Agent request timed out")
        return ChatResponse(
            message="Request timed out",
            error="Agent did not respond within time limit"
        )
    except Exception as e:
        logger.error(f"[-] Unexpected error: {str(e)}")
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
