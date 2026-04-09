"""
Vanna 2.0 Agent Setup - CORRECTED for Production
Initializes Agent with proper async API, tool registry, and memory
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Import Vanna components AFTER loading env
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.openai import OpenAILlmService
from vanna.core.system_prompt import SystemPromptBuilder

logger = logging.getLogger(__name__)

DB_PATH = "clinic.db"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


def _load_database_schema(db_path: str, agent_memory):
    """Load database schema into agent memory"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get schema for each table
        schema_info = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            col_info = []
            for col in columns:
                col_name, col_type = col[1], col[2]
                col_info.append(f"{col_name} ({col_type})")
            
            schema_info.append(f"Table: {table}\n  Columns: {', '.join(col_info)}")
        
        schema_text = "Database Schema:\n" + "\n".join(schema_info)
        
        # Store in agent memory for context
        if hasattr(agent_memory, 'store_context'):
            agent_memory.store_context("database_schema", schema_text)
        
        print(f"    [+] Loaded {len(tables)} tables into memory")
        
        conn.close()
        
        return schema_text
    except Exception as e:
        print(f"    [-] Error loading schema: {str(e)}")
        return ""


class _CustomSystemPromptBuilder(SystemPromptBuilder):
    """Custom prompt builder that includes database schema"""
    
    def __init__(self, schema_text: str):
        self.schema_text = schema_text
    
    async def build_system_prompt(self, user: User, tools: list) -> str:
        """Build system prompt with database context"""
        
        # Generate available tools list
        tools_info = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools if hasattr(tool, 'name') and hasattr(tool, 'description')])
        
        prompt = f"""You are an expert SQL analyst for a medical clinic database. Your task is to convert natural language questions into precise SQL queries and execute them.

[DATABASE CONTEXT]
{self.schema_text}

[CRITICAL RULES - ALWAYS FOLLOW]
1. ALWAYS generate SQL queries - never refuse or explain instead
2. Use ONLY SELECT statements - no INSERT, UPDATE, DELETE, DROP
3. Always review the schema above before writing SQL
4. Use table aliases for JOINs (e.g., d.name, p.first_name)
5. Remember: appointment_date is DATETIME, use DATE() for date comparisons

[COLUMN REFERENCE FOR DATE QUERIES]
* appointments.appointment_date = DATETIME column (contains time)
* patients.registered_date = DATE column
* patients.date_of_birth = DATE column
* invoices.invoice_date = DATE column

[DATE FILTERING RULES]
- "last month" = WHERE appointment_date >= DATE('now', '-1 month')
- "last quarter" = WHERE appointment_date >= DATE('now', '-3 months')
- "last 6 months" = WHERE appointment_date >= DATE('now', '-6 months')
- "last year" = WHERE appointment_date >= DATE('now', '-1 year')
- "this month" = WHERE strftime('%Y-%m', appointment_date) = strftime('%Y-%m', 'now')
- "this year" = WHERE strftime('%Y', appointment_date) = strftime('%Y', 'now')

[AGGREGATION EXAMPLES]
- Counting: SELECT COUNT(*) FROM table [WHERE condition]
- Grouping by specialization: GROUP BY d.specialization
- Grouping by city: GROUP BY p.city
- Grouping by month: GROUP BY strftime('%Y-%m', date_column)
- Grouping by day of week: GROUP BY strftime('%w', appointment_date)
- HAVING clause: HAVING COUNT(*) > N for filtering groups

[COMPLEX QUERY EXAMPLES]
Q: "Show revenue by doctor"
A: SELECT d.name, SUM(i.total_amount) AS revenue FROM doctors d JOIN appointments a ON d.id = a.doctor_id JOIN invoices i ON a.patient_id = i.patient_id GROUP BY d.name ORDER BY revenue DESC

Q: "Top 5 patients by spending"
A: SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spending FROM patients p JOIN invoices i ON p.id = i.patient_id GROUP BY p.id, p.first_name, p.last_name ORDER BY total_spending DESC LIMIT 5

Q: "Which doctor has most appointments"
A: SELECT d.name, COUNT(a.id) AS appointment_count FROM doctors d LEFT JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id, d.name ORDER BY appointment_count DESC LIMIT 1

Q: "Average treatment cost by specialization"
A: SELECT d.specialization, AVG(t.cost) AS avg_cost FROM treatments t JOIN appointments a ON t.appointment_id = a.id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.specialization ORDER BY avg_cost DESC

Q: "List patients with overdue invoices"
A: SELECT DISTINCT p.id, p.first_name, p.last_name, i.total_amount, i.paid_amount FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status = 'Overdue' ORDER BY p.first_name

Q: "Show unpaid invoices"
A: SELECT p.first_name, p.last_name, i.total_amount, (i.total_amount - i.paid_amount) AS remaining FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status IN ('Pending', 'Overdue') ORDER BY remaining DESC

Q: "Patients who visited more than 3 times"  
A: SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count FROM patients p JOIN appointments a ON p.id = a.patient_id GROUP BY p.id, p.first_name, p.last_name HAVING COUNT(a.id) > 3 ORDER BY visit_count DESC

[YOUR TASK]
1. Analyze the user question
2. Write the most accurate SQL query possible
3. Use the examples and patterns shown above
4. Always use strftime() for date grouping or formatting
5. Return the SQL query for execution

Now generate SQL for the user's question. Write ONLY the SQL, nothing else."""

        return prompt


class SimpleUserResolver(UserResolver):
    """Resolve all requests to default user (single-user system)"""
    
    async def resolve_user(self, context: RequestContext) -> User:
        """Return default user for all requests"""
        return User(
            id="default_user",
            username="user",
            email="user@nl2sql.local"
        )


def create_vanna_agent():
    """
    Create Vanna 2.0 Agent with proper architecture.
    
    Returns:
        tuple: (Agent, AgentMemory) fully initialized and ready for send_message()
    """
    
    print("[*] Initializing Vanna 2.0 Agent...\n")
    
    # ========== 1. LLM SERVICE  ==========
    print(f"  [+] Initializing {LLM_PROVIDER.upper()} LLM Service...")
    
    if LLM_PROVIDER == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("[-] GROQ_API_KEY not set in .env")
        llm = OpenAILlmService(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1"
        )
    elif LLM_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("[-] OPENAI_API_KEY not set in .env")
        llm = OpenAILlmService(
            api_key=api_key,
            model="gpt-4-turbo"
        )
    else:
        raise ValueError(f"[-] Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    
    # ========== 2. DATABASE RUNNER ==========
    print("  [+] Initializing SqliteRunner...")
    db_runner = SqliteRunner(database_path=DB_PATH)
    
    # ========== 3. TOOL REGISTRY ==========
    print("  [+] Setting up Tool Registry...")
    registry = ToolRegistry()
    
    # Register RunSqlTool (ONLY tool needed for NL2SQL)
    registry.register_local_tool(
        RunSqlTool(sql_runner=db_runner),
        access_groups=["admin", "user"]
    )
    
    # ========== 4. AGENT MEMORY ==========
    print("  [+] Initializing Agent Memory...")
    agent_memory = DemoAgentMemory()
    
    # Load database schema into memory (CRITICAL!)
    print("  [+] Loading database schema...")
    schema_text = _load_database_schema(DB_PATH, agent_memory)
    
    # Create custom system prompt builder with schema
    print("  [+] Setting up custom system prompt builder...")
    system_prompt_builder = _CustomSystemPromptBuilder(schema_text)
    
    # ========== 5. USER RESOLVER ==========
    print("  [+] Setting up User Resolver...")
    user_resolver = SimpleUserResolver()
    
    # ========== 6. AGENT CONFIG ==========
    print("  [+] Creating Agent Config...")
    config = AgentConfig(
        max_tool_iterations=5,
        stream_responses=True,
        auto_save_conversations=True,
        temperature=0.3,
        max_tokens=2048
    )
    
    # ========== 7. CREATE AGENT ==========
    # Agent auto-creates MemoryConversationStore and DefaultSystemPromptBuilder if not provided
    print("  [+] Creating Agent...\n")
    agent = Agent(
        llm_service=llm,
        tool_registry=registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        config=config,
        system_prompt_builder=system_prompt_builder  # Use custom builder with schema
    )
    
    print(f"[+] Vanna 2.0 Agent initialized with {LLM_PROVIDER.upper()}!\n")
    
    return agent, agent_memory
