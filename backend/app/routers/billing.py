"""
Billing router — Stripe checkout and customer portal.

Endpoints:
  POST /api/billing/checkout  — Create Stripe checkout session
  POST /api/billing/portal    — Create Stripe customer portal session
  GET  /api/billing/status    — Get current subscription status (login reconciliation)
"""

from __future__ import annotations

import structlog
import stripe
from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.db import get_supabase
from app.dependencies import get_current_user
from app.models.requests import CheckoutRequest
from app.models.responses import CheckoutSessionResponse, PortalSessionResponse, CreditStatusResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user: dict = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Create a Stripe checkout session for a Pro subscription.

    The client should redirect to the returned checkout_url.
    client_reference_id is set to the user's ID so the webhook can associate the
    subscription with the correct profile on completion.
    """
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing is not configured")

    stripe.api_key = settings.stripe_secret_key
    user_id = user["sub"]
    user_email = user.get("email", "")

    log = logger.bind(user_id=user_id)

    # Fetch or reuse existing Stripe customer ID
    supabase = get_supabase()
    profile_res = (
        supabase.table("profiles")
        .select("stripe_customer_id")
        .eq("id", user_id)
        .single()
        .execute()
    )
    existing_customer_id = (profile_res.data or {}).get("stripe_customer_id")

    try:
        session_params: dict = {
            "mode": "subscription",
            "line_items": [{"price": request.price_id, "quantity": 1}],
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "client_reference_id": user_id,
        }
        if existing_customer_id:
            session_params["customer"] = existing_customer_id
        elif user_email:
            session_params["customer_email"] = user_email

        session = stripe.checkout.Session.create(**session_params)
    except stripe.error.StripeError as exc:
        log.error("billing.checkout.stripe_error", error=str(exc))
        raise HTTPException(status_code=502, detail="Failed to create checkout session")

    log.info("billing.checkout.created", session_id=session.id)
    return CheckoutSessionResponse(checkout_url=session.url)


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    user: dict = Depends(get_current_user),
) -> PortalSessionResponse:
    """
    Create a Stripe customer portal session for subscription self-management.

    Requires the user to already have a Stripe customer ID (i.e., have subscribed before).
    """
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing is not configured")

    stripe.api_key = settings.stripe_secret_key
    user_id = user["sub"]

    supabase = get_supabase()
    profile_res = (
        supabase.table("profiles")
        .select("stripe_customer_id")
        .eq("id", user_id)
        .single()
        .execute()
    )
    customer_id = (profile_res.data or {}).get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found. Please subscribe first.",
        )

    try:
        portal = stripe.billing_portal.Session.create(customer=customer_id)
    except stripe.error.StripeError as exc:
        logger.error("billing.portal.stripe_error", user_id=user_id, error=str(exc))
        raise HTTPException(status_code=502, detail="Failed to create portal session")

    logger.info("billing.portal.created", user_id=user_id)
    return PortalSessionResponse(portal_url=portal.url)


@router.get("/status", response_model=CreditStatusResponse)
async def get_billing_status(
    user: dict = Depends(get_current_user),
) -> CreditStatusResponse:
    """
    Return current credit and subscription status.

    Also reconciles the user's tier with Stripe if the subscription state has drifted
    (e.g., user opened multiple tabs or had a lapsed session).
    """
    settings = get_settings()
    supabase = get_supabase()
    user_id = user["sub"]

    profile_res = (
        supabase.table("profiles")
        .select("tier,credits_used,daily_credit_limit,credits_reset_at,stripe_subscription_id")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_res.data

    # Live Stripe reconciliation: if we have a subscription ID, check its current status
    sub_id = profile.get("stripe_subscription_id")
    if sub_id and settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
        try:
            sub = stripe.Subscription.retrieve(sub_id)
            expected_tier = "pro" if sub.status == "active" else "core"
            if profile["tier"] != expected_tier:
                supabase.table("profiles").update({"tier": expected_tier}).eq(
                    "id", user_id
                ).execute()
                profile["tier"] = expected_tier
                logger.info(
                    "billing.status.reconciled",
                    user_id=user_id,
                    tier=expected_tier,
                    stripe_status=sub.status,
                )
        except stripe.error.StripeError as exc:
            logger.warning("billing.status.reconcile_failed", user_id=user_id, error=str(exc))

    credits_used = profile.get("credits_used", 0)
    limit = profile.get("daily_credit_limit", 3)

    return CreditStatusResponse(
        credits_used=credits_used,
        daily_credit_limit=limit,
        credits_remaining=max(0, limit - credits_used),
        reset_at=profile.get("credits_reset_at"),
        tier=profile.get("tier", "core"),
    )
