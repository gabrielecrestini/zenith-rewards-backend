from fastapi import APIRouter, Depends, HTTPException
import logging
from ..managers import AIManager
from ..models import AIAdviceRequest, AIGenerationRequest, VoteContentRequest

router = APIRouter(
    prefix="/ai",
    tags=["Artificial Intelligence"]
)
logger = logging.getLogger(__name__)

def get_ai_manager():
    return AIManager()

@router.post("/generate-advice")
async def generate_advice_endpoint(req: AIAdviceRequest, ai_manager: AIManager = Depends(get_ai_manager)):
    try:
        return await ai_manager.generate_advice(req)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in generate_advice_endpoint for user {req.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/generate")
async def generate_content_endpoint(req: AIGenerationRequest, ai_manager: AIManager = Depends(get_ai_manager)):
    try:
        return await ai_manager.generate_content(req)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in generate_content_endpoint for user {req.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/content/{ai_content_id}/publish")
def publish_content_endpoint(ai_content_id: int, ai_manager: AIManager = Depends(get_ai_manager)):
    try:
        return ai_manager.publish_ai_content(ai_content_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in publish_content_endpoint for content {ai_content_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/content/feed")
async def get_content_feed_endpoint(ai_manager: AIManager = Depends(get_ai_manager)):
    try:
        return await ai_manager.get_feed()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in get_content_feed_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/content/{content_id}/vote")
async def vote_content_endpoint(content_id: int, req: VoteContentRequest, ai_manager: AIManager = Depends(get_ai_manager)):
    try:
        return await ai_manager.vote_content(content_id, req.user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in vote_content_endpoint for content {content_id} by user {req.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")