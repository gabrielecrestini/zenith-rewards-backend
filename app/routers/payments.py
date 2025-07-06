import os
from fastapi import APIRouter, Request, Response, HTTPException, Depends
import logging
import stripe

from ..models import CreateSubscriptionRequest
from ..database import _execute_pg_query
from ..managers import ShopManager, UserManager
from ..models import SubscriptionPlan

router = APIRouter(
    tags=["Payments"]
)
logger = logging.getLogger(__name__)

# --- Load Stripe Configuration ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID_PREMIUM = os.environ.get("STRIPE_PRICE_ID_PREMIUM")
STRIPE_PRICE_ID_ASSISTANT = os.environ.get("STRIPE_PRICE_ID_ASSISTANT")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

def get_user_manager():
    return UserManager()
    
def get_shop_manager():
    return ShopManager()

@router.post("/create-checkout-session")
def create_checkout_session_endpoint(req: CreateSubscriptionRequest, user_manager: UserManager = Depends(get_user_manager)):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured.")

    price_map = {
        'premium': STRIPE_PRICE_ID_PREMIUM,
        'assistant': STRIPE_PRICE_ID_ASSISTANT
    }
    price_id = price_map.get(req.plan_type)
    
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan type specified.")
    
    try:
        user_profile_data = user_manager.get_user_profile(req.user_id)
        # Note: We need the user's email for creating a Stripe customer. 
        # The profile endpoint in the original code didn't return it. We assume it's available or fetch it.
        # For this example, let's fetch it directly.
        user_record = _execute_pg_query("SELECT email, stripe_customer_id FROM users WHERE user_id = %s", (req.user_id,), fetch_one=True)
        
        if not user_record:
            raise HTTPException(status_code=404, detail="User not found.")

        user_email = user_record.get('email')
        customer_id = user_record.get('stripe_customer_id')
        
        if not customer_id:
            logger.info(f"Creating new Stripe customer for user {req.user_id}.")
            customer = stripe.Customer.create(
                email=user_email,
                metadata={'user_id': req.user_id}
            )
            customer_id = customer.id
            _execute_pg_query(
                "UPDATE users SET stripe_customer_id = %s WHERE user_id = %s",
                (customer_id, req.user_id), error_context="update user with Stripe customer ID"
            )
        
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata={
                'user_id': req.user_id,
                'plan_type': req.plan_type
            }
        )
        logger.info(f"Stripe Checkout Session created for user {req.user_id}.")
        return {"url": checkout_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e.user_message}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stripe error: {e.user_message}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.critical(f"Unhandled exception in create_checkout_session_endpoint for user {req.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, shop_manager: ShopManager = Depends(get_shop_manager)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    if not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured. Cannot process webhooks.")
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured.")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        logger.error(f"Invalid payload for Stripe webhook: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature for Stripe webhook: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing Stripe webhook event: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    event_type = event['type']
    data_object = event['data']['object']
    logger.info(f"Received Stripe webhook event type: {event_type}")

    if event_type == 'customer.subscription.created' or event_type == 'customer.subscription.updated':
        subscription = data_object
        customer_id = subscription.get('customer')
        price_id = subscription['items']['data'][0]['price']['id']
        status = subscription.get('status')
        
        user_res = _execute_pg_query("SELECT user_id FROM users WHERE stripe_customer_id = %s", (customer_id,), fetch_one=True, error_context="fetch user for subscription webhook")
        
        if user_res:
            user_id = user_res['user_id']
            new_plan = SubscriptionPlan.FREE.value
            
            if price_id == STRIPE_PRICE_ID_PREMIUM:
                new_plan = SubscriptionPlan.PREMIUM.value
            elif price_id == STRIPE_PRICE_ID_ASSISTANT:
                new_plan = SubscriptionPlan.ASSISTANT.value
            
            if status in ['active', 'trialing']:
                _execute_pg_query("UPDATE users SET subscription_plan = %s WHERE user_id = %s", (new_plan, user_id), error_context="update user subscription plan")
                logger.info(f"User {user_id} subscription plan updated to {new_plan} (status: {status}).")
            else:
                _execute_pg_query("UPDATE users SET subscription_plan = %s WHERE user_id = %s", (SubscriptionPlan.FREE.value, user_id), error_context="revert user subscription plan")
                logger.info(f"User {user_id} subscription plan reverted to FREE (status: {status}).")
        else:
            logger.warning(f"User not found for Stripe customer ID: {customer_id} during subscription webhook.")

    elif event_type == 'customer.subscription.deleted':
        customer_id = data_object.get('customer')
        user_res = _execute_pg_query("SELECT user_id FROM users WHERE stripe_customer_id = %s", (customer_id,), fetch_one=True, error_context="fetch user for deleted subscription webhook")
        if user_res:
            _execute_pg_query("UPDATE users SET subscription_plan = %s WHERE user_id = %s", (SubscriptionPlan.FREE.value, user_res['user_id']), error_context="revert user plan on subscription delete")
            logger.info(f"User {user_res['user_id']} subscription deleted, reverted to FREE plan.")
        else:
            logger.warning(f"User not found for Stripe customer ID: {customer_id} during deleted subscription webhook.")
            
    elif event_type == 'payment_intent.succeeded':
        payment_intent = data_object
        user_id = payment_intent['metadata'].get('user_id')
        item_id = payment_intent['metadata'].get('item_id')
        
        if user_id and item_id:
            item = _execute_pg_query("SELECT id, name, description, price_points, price_eur, item_type, effect, image_url, is_active FROM shop_items WHERE id = %s", (int(item_id),), fetch_one=True, error_context="fetch item for payment intent succeeded")
            if item:
                await shop_manager._apply_item_effect(user_id, item, 'stripe', None, item.get('price_eur'))
                logger.info(f"Payment intent succeeded for user {user_id}, item {item['name']}. Effect applied.")
            else:
                logger.warning(f"Item {item_id} not found for successful payment intent for user {user_id}.")
        else:
            logger.warning(f"Missing user_id or item_id in metadata for payment_intent.succeeded: {payment_intent['metadata']}")

    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return Response(status_code=200)