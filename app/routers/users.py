# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException
import logging
from ..managers import UserManager
from ..models import UserSyncRequest, UserProfileUpdate, PayoutRequest
from ..database import _execute_pg_query

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
logger = logging.getLogger(__name__)

POINTS_TO_EUR_RATE = 1000.0

def get_user_manager(): return UserManager()

@router.post("/sync")
def sync_user_endpoint(user_data: UserSyncRequest, user_manager: UserManager = Depends(get_user_manager)):
    # ... (il codice degli endpoint relativi agli utenti va qui)
    # Esempio:
    try:
        return user_manager.sync_user(user_data)
    except HTTPException as e:
        logger.error(f"HTTPException in sync_user_endpoint: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in sync_user_endpoint for user {user_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during user sync: {str(e)}")

# ... Incolla qui tutti gli altri endpoint relativi a:
# - /update_profile/{user_id}
# - /request_payout  (ricorda di spostare la logica dell'endpoint qui)
# - /{user_id}/profile
# - /balance/{user_id}
# - /streak/status/{user_id}
# - /streak/claim/{user_id}
# - /referral_stats/{user_id}