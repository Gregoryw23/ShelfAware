# ShelfAware AI Coding Agent Instructions

## Project Overview

**ShelfAware** is a FastAPI-based community-driven book synopsis system. The core innovation: users add personal synopses to their bookshelves, then a daily automated cron job aggregates these user synopses and generates polished community synopses using OpenAI LLM.

## Architecture & Key Components

### Data Flow Architecture
1. **User Input**: Users add books to bookshelves with personal synopses (`Bookshelf.synopsis`)
2. **Daily Sync**: Scheduler (`SynopsisScheduler`) triggers at midnight UTC (configurable)
3. **LLM Pipeline**: `SynopsisSyncService` extracts user synopses → groups by book → generates community synopsis via GPT-3.5-turbo
4. **Storage**: Generated community synopses stored in `Book.CommunitySynopsis` for display

### Service Boundaries
- **`SynopsisScheduler`** ([app/services/synopsis_scheduler.py](app/services/synopsis_scheduler.py)): Manages APScheduler cron job lifecycle (init → start/stop)
- **`SynopsisSyncService`** ([app/services/synopsis_sync_service.py](app/services/synopsis_sync_service.py)): LLM orchestration and synopsis generation logic
- **Auth Routes** ([app/routes/auth.py](app/routes/auth.py)): User registration, password reset (JWT-based, Cognito roles planned)

### Database Schema (SQLAlchemy ORM)
- **User** → has many Bookshelves (one-to-many)
- **Book** → has many Bookshelves (one-to-many)
- **Bookshelf** (join table): User + Book with metadata (`shelf_status`, `synopsis`, `date_started`, `date_finished`)
- UUIDs for primary keys on User/Book; composite primary key on Bookshelf

## Critical Patterns & Conventions

### Service Instantiation Pattern
Services are singleton-pattern initialized in startup event:
```python
@app.on_event("startup")
async def startup_event():
    SynopsisScheduler.initialize(openai_api_key=openai_api_key)
    SynopsisScheduler.start(hour=0, minute=0)  # Customize schedule here
```
Don't create new service instances—use class methods on schedulers/services.

### Dependency Injection
All endpoints receive `db: Session = Depends(get_db)` via [app/dependencies/db.py](app/dependencies/db.py). Keep this pattern for DB access.

### Error Handling
Errors are logged via `logger.error()` but LLM failures should gracefully degrade (return None synopsis rather than crash). See [app/services/synopsis_sync_service.py](app/services/synopsis_sync_service.py) line 70+.

### Schema & Pydantic Models
Mix: Some models defined in `models/` (SQLAlchemy ORM) + schema validation in `schemas/` directory. For new models, follow existing pattern (see [app/models/book.py](app/models/book.py) for dual SQLAlchemy + Pydantic definition).

## Developer Workflows

### Running the Application
```bash
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
uvicorn app.main:app --reload
```

### Database Migrations (Alembic)
```bash
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```
Migrations tracked in [migrations/versions/](migrations/versions/).

### Manual Synopsis Sync (for testing)
```bash
curl -X POST http://localhost:8000/admin/sync-synopses
```

### Key Dependencies
- **FastAPI** (0.115.6): Web framework
- **SQLAlchemy** (2.0.36): ORM with SQLite backend
- **APScheduler** (3.10.4): Cron job scheduling
- **OpenAI** (1.59.3): LLM API for synopsis generation
- **python-jose** + **passlib[bcrypt]**: Auth/password hashing

## Integration Points & Externals

### OpenAI Integration
- Initialized in `startup_event()` with `OPENAI_API_KEY` env var
- Uses `gpt-3.5-turbo` model (max_tokens=250, temperature=0.7)
- **Failure mode**: If key missing, scheduler silently disabled; no synopses generated

### Database (SQLite)
- File: `app.db` in project root (configured in [app/db/database.py](app/db/database.py))
- Initialized on app startup: `Base.metadata.create_all(bind=engine)`

### Authentication (Future: Cognito)
- Currently: JWT in headers (see [app/core/security.py](app/core/security.py) for hash_password)
- Cognito role support scaffolded in [app/dependencies/auth.py](app/dependencies/auth.py) but not active yet

## When Adding Features

1. **New endpoint**: Add to `app/routes/` with router prefix, use `get_db` dependency
2. **New model**: Define in `app/models/` with Base inheritance, add Pydantic schemas
3. **New service logic**: Create in `app/services/`, inject DB via `SessionLocal` or endpoint dependency
4. **External API calls**: Follow OpenAI pattern—initialize in startup, handle errors gracefully
5. **Scheduled jobs**: Register with `SynopsisScheduler.add_job()` before calling `start()`

## Testing Notes

- No pytest suite currently present; manual testing via `/admin/sync-synopses` endpoint
- Logs available in console (basicConfig at app/main.py:10)
- SQLite allows local testing without external DB setup

## Project-Specific Conventions

- **Naming**: Bookshelf fields use camelCase (`shelf_status`, `date_started`); models use snake_case
- **UUIDs**: Generated via `str(uuid.uuid4())` or `uuid.uuid4()`—do not use sequential IDs
- **Timestamps**: Use `datetime.utcnow()` for consistency (UTC only)
- **Column definitions**: Use `server_default=text("'active'")` for defaults, not Python defaults
