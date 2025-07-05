# app/routers/general.py

from fastapi import APIRouter, Depends, HTTPException
import logging
from ..managers import ContestManager, ShopManager, UserManager
from ..models import ShopBuyRequest, SubscriptionPlan

router = APIRouter(
    tags=["General"]
)
logger = logging.getLogger(__name__)

def get_contest_manager(): return ContestManager()
def get_shop_manager(): return ShopManager()
def get_user_manager(): return UserManager()

@router.get("/leaderboard")
def get_leaderboard_endpoint(contest_manager: ContestManager = Depends(get_contest_manager)):
    # ... codice dell'endpoint ...

# ... Incolla qui tutti gli altri endpoint relativi a:
# - /contests/current/{user_id}
# - /shop/items
# - /shop/buy