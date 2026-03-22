import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.cognito_service import RoleChecker, CognitoAdminRole
from app.services.synopsis_sync_service import SynopsisSyncService
from app.dependencies.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/users", dependencies=[Depends(RoleChecker("Admins"))])
def list_users():
    return {"message": "Admin access granted"}


@router.post("/generate-community-reviews")
async def generate_community_reviews(db: Session = Depends(get_db)):
    """
    Manually trigger community review generation for all books.
    
    This endpoint:
    1. Retrieves all user review texts grouped by book_id
    2. Groups them by book_id
    3. For each book, determines if significant changes have occurred
    4. If changes are significant, generates a proposed community review using OpenAI LLM
    5. Creates/refreshes moderation queue items for accept/reject
    
    Response:
    {
        "status": "success",
        "timestamp": "2026-03-09T...",
        "total_books_processed": 5,
        "updated": 3,
        "skipped": 2,
        "errors": []
    }
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured. Cannot generate community reviews."
            )
        
        logger.info("Manual community review generation initiated")
        
        # Initialize service and run sync
        service = SynopsisSyncService(openai_api_key=openai_api_key)
        result = service.generate_all_community_reviews(db)
        
        logger.info(f"Manual community review generation completed: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during manual community review generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during community review generation: {str(e)}"
        )


@router.post("/sync-synopses")
async def sync_synopses_manual(db: Session = Depends(get_db)):
    """Legacy alias: use /admin/generate-community-reviews instead."""
    return await generate_community_reviews(db)


@router.get("/synopsis-moderation")
def list_synopsis_moderation(
    status: str = Query(default="pending", pattern="^(pending|accepted|rejected|all)$"),
    db: Session = Depends(get_db),
):
    try:
        service = SynopsisSyncService(openai_api_key=os.getenv("OPENAI_API_KEY", ""))
        items = service.list_moderation_items(db, status_filter=status)
        return {
            "status": "success",
            "count": len(items),
            "items": items,
        }
    except Exception as e:
        logger.error(f"Error listing synopsis moderation items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list moderation items: {str(e)}")


@router.post("/synopsis-moderation/{moderation_id}/accept")
def accept_synopsis_moderation(moderation_id: str, db: Session = Depends(get_db)):
    try:
        service = SynopsisSyncService(openai_api_key=os.getenv("OPENAI_API_KEY", ""))
        result = service.accept_moderation_item(db, moderation_id)
        return {"status": "success", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error accepting synopsis moderation item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to accept moderation item: {str(e)}")


@router.post("/synopsis-moderation/{moderation_id}/reject")
def reject_synopsis_moderation(moderation_id: str, db: Session = Depends(get_db)):
    try:
        service = SynopsisSyncService(openai_api_key=os.getenv("OPENAI_API_KEY", ""))
        result = service.reject_moderation_item(db, moderation_id)
        return {"status": "success", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting synopsis moderation item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject moderation item: {str(e)}")