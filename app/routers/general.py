from fastapi import APIRouter, Depends, HTTPException
import logging
from ..managers import ContestManager, ShopManager, UserManager
from ..models import ShopBuyRequest, SubscriptionPlan

router = APIRouter(
    tags=["General"]
)
logger = logging.getLogger(__name__)

def get_contest_manager():
    return ContestManager()

def get_shop_manager():
    return ShopManager()

def get_user_manager():
    return UserManager()

@router.get("/leaderboard")
def get_leaderboard_endpoint(contest_manager: ContestManager = Depends(get_contest_manager)):
    try:
        return contest_manager.get_leaderboard()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in get_leaderboard_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/contests/current/{user_id}")
def get_current_contest_endpoint(user_id: str, contest_manager: ContestManager = Depends(get_contest_manager), user_manager: UserManager = Depends(get_user_manager)):
    try:
        user_profile = user_manager.get_user_profile(user_id)
        user_plan = SubscriptionPlan(user_profile.get('subscription_plan', SubscriptionPlan.FREE.value))
        contest = contest_manager.get_current_contest(user_plan)
        if not contest:
            raise HTTPException(status_code=404, detail="Nessun contest attivo disponibile per il tuo piano al momento.")
        return contest
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in get_current_contest_endpoint for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/shop/items")
def get_shop_items_endpoint(shop_manager: ShopManager = Depends(get_shop_manager)):
    try:
        return shop_manager.get_shop_items()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in get_shop_items_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/shop/buy")
async def buy_shop_item_endpoint(req: ShopBuyRequest, shop_manager: ShopManager = Depends(get_shop_manager)):
    try:
        return await shop_manager.buy_item(req)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in buy_shop_item_endpoint for user {req.user_id}, item {req.item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")