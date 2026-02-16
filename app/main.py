# import logging
# import os
# from fastapi import FastAPI
# from app.db.database import engine, Base
# from app.models import user, mood, book, bookshelf, password_reset
# from app.services.synopsis_scheduler import SynopsisScheduler
# from app.routes import auth # Import authentication routes
# <<<<<<< feature/jwt-auth-rbac
# from app.routes.admin import router as admin_router
# =======
# from app.routes import bookshelf #Import bookshelf routes
# from app.routes.auth import router as auth_router
# from app.routes.bookshelf import router as bookshelf_router

# >>>>>>> main

#Resolving conflicting auth call for both bookshelf and auth_router
import logging
import os
from fastapi import FastAPI
from app.db.database import engine, Base
from app.models import user, bookshelf, password_reset
from app.services.synopsis_scheduler import SynopsisScheduler
from app.routes import auth, books, bookshelves
from app.routes.admin import router as admin_router
from app.routes.bookshelf import router as bookshelf_router
from app.routes import chroma # Import ChromaDB search routes
from app.routes import user_profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShelfAware API",
    description="An API for managing books and integrating with Ollama and ChromaDB",
    version="0.1.0",
)

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(bookshelves.router, prefix="/bookshelves", tags=["Bookshelves"])


# Initialize and start synopsis scheduler on startup
@app.on_event("startup")
async def startup_event():
    """Initialize and start the synopsis sync scheduler."""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY environment variable not set. Synopsis sync disabled.")
            return
        
        # Initialize scheduler
        SynopsisScheduler.initialize(openai_api_key=openai_api_key)
        
        # Start scheduler (runs daily at midnight UTC by default)
        # Customize with: SynopsisScheduler.start(hour=2, minute=30)  # runs at 2:30 AM UTC
        SynopsisScheduler.start(hour=0, minute=0)  # runs daily at midnight UTC
        
        logger.info("Synopsis scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start synopsis scheduler: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler on shutdown."""
    SynopsisScheduler.stop()

@app.get("/")
def home():
    return {"message": "Welcome to ShelfAware"}

@app.post("/admin/sync-synopses")
def trigger_manual_sync():
    """
    Manual endpoint to trigger synopsis synchronization.
    Useful for testing and on-demand updates.
    
    Requires admin access in production.
    """
    try:
        result = SynopsisScheduler.add_manual_job()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Manual sync failed: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    from app.routes import bookshelf

# For bookshelf
#app.include_router(bookshelf.router, prefix="/bookshelf", tags=["bookshelf"])
app.include_router(admin_router)
app.include_router(bookshelf_router)

#for user profile
app.include_router(user_profile.router)