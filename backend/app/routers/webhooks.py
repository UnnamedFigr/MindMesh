"""
Webhooks router — external service webhooks.

Endpoints:
  POST /api/webhooks/stripe  — Handle Stripe webhook events
"""

from __future__ import annotations

import stripe
import structlog
from fastapi import APIRouter, Header, HTTPException, Request

from app.config import get_settings

logger = structlog.get_logger()

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
):
    """
    Handle Stripe webhook events for subscription management.

    Events handled:
    - checkout.session.completed — New subscription
    - customer.subscription.updated — Plan change
    - customer.subscription.deleted — Cancellation
    - invoice.payment_failed — Payment failure
    """
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    # Verify webhook signature
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("stripe.webhook.invalid_signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as exc:
        logger.error("stripe.webhook.parse_error", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("stripe.webhook.received", event_type=event_type)

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(data)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(data)
        else:
            logger.debug("stripe.webhook.unhandled", event_type=event_type)
    except Exception as exc:
        logger.error("stripe.webhook.handler_error", event_type=event_type, error=str(exc))
        # Return 200 anyway to prevent Stripe retries for handler errors
        # The issue will be logged and can be investigated

    return {"status": "ok"}


async def _handle_checkout_completed(data: dict) -> None:
    """Handle successful checkout — activate Pro subscription."""
    supabase = _get_supabase()
    user_id = data.get("client_reference_id")  # Set during checkout session creation
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")

    if not user_id:
        logger.error("stripe.checkout.no_user_id", data=data)
        return

    # Upgrade user to Pro
    supabase.table("profiles").update({
        "tier": "pro",
        "daily_credit_limit": 15,  # Pro tier: 15 credits/day
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
    }).eq("id", user_id).execute()

    logger.info("stripe.checkout.completed", user_id=user_id, subscription_id=subscription_id)


async def _handle_subscription_updated(data: dict) -> None:
    """Handle subscription changes (upgrades, downgrades)."""
    supabase = _get_supabase()
    subscription_id = data.get("id")
    status = data.get("status")

    # Find user by subscription ID
    response = (
        supabase.table("profiles")
        .select("id")
        .eq("stripe_subscription_id", subscription_id)
        .single()
        .execute()
    )

    if not response.data:
        logger.warning("stripe.subscription.user_not_found", subscription_id=subscription_id)
        return

    user_id = response.data["id"]

    if status == "active":
        supabase.table("profiles").update({
            "tier": "pro",
            "daily_credit_limit": 15,
        }).eq("id", user_id).execute()
    elif status in ("past_due", "unpaid"):
        logger.warning("stripe.subscription.payment_issue", user_id=user_id, status=status)

    logger.info("stripe.subscription.updated", user_id=user_id, status=status)


async def _handle_subscription_deleted(data: dict) -> None:
    """Handle subscription cancellation — downgrade to free."""
    supabase = _get_supabase()
    subscription_id = data.get("id")

    response = (
        supabase.table("profiles")
        .select("id")
        .eq("stripe_subscription_id", subscription_id)
        .single()
        .execute()
    )

    if not response.data:
        return

    user_id = response.data["id"]

    supabase.table("profiles").update({
        "tier": "core",
        "daily_credit_limit": 3,  # Core tier: 3 credits/day
        "stripe_subscription_id": None,
    }).eq("id", user_id).execute()

    logger.info("stripe.subscription.cancelled", user_id=user_id)


async def _handle_payment_failed(data: dict) -> None:
    """Log payment failure for monitoring."""
    customer_id = data.get("customer")
    logger.warning("stripe.payment.failed", customer_id=customer_id)


def _get_supabase():
    """Get Supabase client via the shared singleton."""
    from app.db import get_supabase
    return get_supabase()
