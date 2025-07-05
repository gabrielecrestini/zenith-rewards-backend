# app/routers/ai.py

from fastapi import APIRouter, Depends, HTTPException
import logging
from ..managers import AIManager
from ..models import AIAdviceRequest, AIGenerationRequest, VoteContentRequest

router = APIRouter(
    prefix="/ai",
    tags=["Artificial Intelligence"]
)
logger = logging.getLogger(__name__)

def get_ai_manager(): return AIManager()

@router.post("/generate-advice")
async def generate_advice_endpoint(req: AIAdviceRequest, ai_manager: AIManager = Depends(get_ai_manager)):
    # ... codice dell'endpoint...

# ... Incolla qui tutti gli altri endpoint relativi a:
# - /generate
# - /content/{ai_content_id}/publish
# - /content/feed
# - /content/{content_id}/vote