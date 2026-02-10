import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.database import SessionLocal
from app.services.synopsis_sync_service import SynopsisSyncService

logger = logging.getLogger(__name__)


class SynopsisScheduler:
    """
    Manages the scheduled cron job for synopsis synchronization.
    """
    
    _scheduler = None
    _service = None

    @classmethod
    def initialize(cls, openai_api_key: str):
        """
        Initialize the scheduler with the synopsis sync service.
        
        Args:
            openai_api_key: OpenAI API key for LLM operations
        """
        if cls._scheduler is None:
            cls._service = SynopsisSyncService(openai_api_key=openai_api_key)
            cls._scheduler = BackgroundScheduler()
            logger.info("SynopsisScheduler initialized")

    @classmethod
    def start(cls, hour: int = 0, minute: int = 0):
        """
        Start the scheduler with a daily cron job.
        
        Args:
            hour: Hour to run job (0-23, default 0 = midnight UTC)
            minute: Minute to run job (0-59, default 0)
        """
        if cls._scheduler is None:
            raise RuntimeError("Scheduler not initialized. Call initialize() first.")
        
        if cls._scheduler.running:
            logger.warning("Scheduler already running")
            return
        
        try:
            # Add daily job
            cls._scheduler.add_job(
                func=cls._sync_job,
                trigger=CronTrigger(hour=hour, minute=minute),
                id="synopsis_sync_daily",
                name="Daily Synopsis Sync",
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )
            
            cls._scheduler.start()
            logger.info(f"Synopsis scheduler started - runs daily at {hour:02d}:{minute:02d} UTC")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            raise

    @classmethod
    def stop(cls):
        """Stop the scheduler."""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("Synopsis scheduler stopped")

    @classmethod
    def _sync_job(cls):
        """
        The actual job function that runs on schedule.
        Executes the synopsis synchronization.
        """
        db = SessionLocal()
        try:
            logger.info("Running scheduled synopsis sync job...")
            result = cls._service.sync_all_synopses(db)
            logger.info(f"Sync job completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in scheduled synopsis sync job: {str(e)}")
            
        finally:
            db.close()

    @classmethod
    def get_scheduler(cls):
        """Get the scheduler instance."""
        return cls._scheduler

    @classmethod
    def add_manual_job(cls, book_id: str = None) -> dict:
        """
        Manually trigger a synopsis sync for specific or all books.
        Useful for on-demand updates.
        
        Args:
            book_id: Optional specific book to sync
            
        Returns:
            Sync result dictionary
        """
        if cls._service is None:
            raise RuntimeError("Service not initialized")
        
        db = SessionLocal()
        try:
            logger.info(f"Running manual synopsis sync job (book_id: {book_id})")
            result = cls._service.sync_all_synopses(db)
            return result
            
        except Exception as e:
            logger.error(f"Error in manual synopsis sync: {str(e)}")
            raise
            
        finally:
            db.close()
