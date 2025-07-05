# app/models.py

from enum import Enum
from pydantic import BaseModel
from typing import Literal

# --- Enums ---
class SubscriptionPlan(str, Enum):
    FREE = 'free'
    PREMIUM = 'premium'
    ASSISTANT = 'assistant'

class ContentType(str, Enum):
    IMAGE = 'IMAGE'
    POST = 'POST'
    VIDEO = 'VIDEO'

class ItemType(str, Enum):
    BOOST = 'BOOST'
    COSMETIC = 'COSMETIC'
    GENERATION_PACK = 'GENERATION_PACK'

# --- Pydantic Models for API Requests ---
class UserSyncRequest(BaseModel):
    user_id: str
    email: str | None = None
    displayName: str | None = None
    referrer_id: str | None = None
    avatar_url: str | None = None

class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None

class PayoutRequest(BaseModel):
    user_id: str
    points_amount: int
    method: str
    address: str

class AIAdviceRequest(BaseModel):
    user_id: str
    prompt: str

class AIGenerationRequest(BaseModel):
    user_id: str
    prompt: str
    content_type: ContentType
    payment_method: Literal['points', 'stripe']
    contest_id: int | None = None

class VoteContentRequest(BaseModel):
    user_id: str

class CreateSubscriptionRequest(BaseModel):
    user_id: str
    plan_type: str
    success_url: str
    cancel_url: str

class ShopBuyRequest(BaseModel):
    user_id: str
    item_id: int
    payment_method: Literal['points', 'stripe']