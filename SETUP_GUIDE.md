# NL2SQL System - Complete Setup Guide

## Quick Start (One Command)

Run the complete setup with a single command:

```bash
pip install -r requirements.txt && python setup_database.py && python seed_memory.py && uvicorn main:app --port 8000
```

This command will:
1. **Install all Python dependencies** from requirements.txt
2. **Setup the SQLite database** with clinic data (patients, doctors, appointments, etc.)
3. **Seed agent memory** with high-quality Q&A pairs for Vanna agent
4. **Start the NL2SQL backend API** on port `http://localhost:8000`

## What Gets Started

### Backend API
- **URL**: `http://localhost:8000`
- **Endpoints**:
  - `POST /chat` - Convert natural language to SQL and execute
  - `GET /health` - Health check endpoint
  - `GET /cache-stats` - Cache statistics

### Features
- ✅ Query Caching (LRU with TTL)
- ✅ Rate Limiting (10 requests/minute per IP)
- ✅ Input Validation (length, SQL injection detection)
- ✅ Structured Logging (rotating files)
- ✅ Chart Generation (Plotly)

## Frontend Setup (Separate)

The frontend is a Next.js application. To run it:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000` in your browser.

**Frontend API Configuration**: Automatically configured to connect to `http://localhost:8000`

## Database

### Schema
- `patients` (200 records)
- `doctors` (15 records)
- `appointments` (500+ records)
- `treatments` (350+ records)
- `invoices` (300+ records)

### Location
- File: `clinic.db` (SQLite)
- Created automatically by `setup_database.py`

## Environment Variables

Located in `.env`:
```
LLM_PROVIDER=groq
GROQ_API_KEY=<your_api_key>
API_HOST=localhost
API_PORT=8000
ENVIRONMENT=development
DEBUG=True
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Sample Query
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients do we have?"}'
```

### Run Test Suite
```bash
python test_20_questions_comprehensive.py
```

## Troubleshooting

### "Groq API rate limit exceeded"
- Check if you've exceeded the free tier limits (100K tokens/day)
- Use a different API key or wait until the limit resets

### "Address already in use" on port 8000
- Another process is using port 8000
- Kill it: `lsof -i :8000` (Linux/Mac) or `netstat -ano | findstr :8000` (Windows)

### Frontend can't connect to backend
- Ensure both are running on correct ports (8000 for backend, 3000 for frontend)
- Check `frontend/.env.local` points to `http://localhost:8000`
- Check browser console for CORS errors

## Performance

- **Cache Hit**: ~1-10ms (returns from cache)
- **Cache Miss**: 1-3 seconds (API call + SQL execution)
- **Cold Start**: 2-5 seconds (first initialization)

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Frontend (Next.js) - Port 3000        │
├─────────────────────────────────────────────────┤
│                     ↓
│          Backend API (FastAPI) - Port 8000      │
│  ├─ Input Validation
│  ├─ Query Caching
│  ├─ Rate Limiting
│  ├─ Vanna 2.0 Agent (Groq LLM)
│  └─ SQLite Database (clinic.db)
└─────────────────────────────────────────────────┘
```

## Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `vanna[sqlite]>=2.0.0` - NL2SQL engine
- `groq` - LLM provider

### Features
- `plotly` - Chart generation
- `pandas` - Data processing
- `slowapi` - Rate limiting

### Database
- `sqlalchemy` - ORM
- `sqlite3` - Database (included with Python)

See `requirements.txt` for complete list.

## Support

For issues or questions, check the GitHub repository or documentation files.
