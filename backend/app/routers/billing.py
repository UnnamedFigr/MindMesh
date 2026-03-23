"""
Billing router — Stripe checkout and customer portal.

Endpoints:
  POST /api/billing/checkout  — Create Stripe checkout session
  POST /api/billing/activate  — Activate Pro from Stripe checkout session (session-ID path)
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


@router.post("/activate", response_model=CreditStatusResponse)
async def activate_checkout_session(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> CreditStatusResponse:
    """
    Activate Pro subscription from a completed Stripe checkout session.

    Called client-side after Stripe redirects to the success URL with a
    session_id query parameter. Works without webhooks — required for local
    development where Stripe cannot reach localhost.

    Security: verifies client_reference_id on the session matches the
    authenticated user, so no user can activate another user's session.
    """
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing is not configured")

    stripe.api_key = settings.stripe_secret_key
    user_id = user["sub"]
    log = logger.bind(user_id=user_id, session_id=session_id)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as exc:
        log.error("billing.activate.stripe_error", error=str(exc))
        raise HTTPException(status_code=502, detail="Failed to retrieve checkout session")

    # Security: verify this session belongs to the requesting user
    if session.client_reference_id != user_id:
        log.warning("billing.activate.user_mismatch", session_user=session.client_reference_id)
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    # Only activate for paid sessions
    if session.payment_status not in ("paid", "no_payment_required"):
        log.warning("billing.activate.not_paid", status=session.payment_status)
        raise HTTPException(status_code=400, detail="Payment not completed")

    customer_id = session.customer
    subscription_id = session.subscription

    supabase = get_supabase()
    supabase.table("profiles").update({
        "tier": "pro",
        "daily_credit_limit": 15,
        "credits_used": 0,
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
    }).eq("id", user_id).execute()

    log.info("billing.activate.success", subscription_id=subscription_id)

    # Return updated credit status
    profile_res = (
        supabase.table("profiles")
        .select("tier,credits_used,daily_credit_limit,credits_reset_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    profile = profile_res.data or {}
    limit = profile.get("daily_credit_limit", 15)
    used = profile.get("credits_used", 0)

    return CreditStatusResponse(
        credits_used=used,
        daily_credit_limit=limit,
        credits_remaining=max(0, limit - used),
        reset_at=profile.get("credits_reset_at"),
        tier=profile.get("tier", "pro"),
    )


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
                update_fields: dict = {"tier": expected_tier}
                if expected_tier == "pro":
                    update_fields["daily_credit_limit"] = 15
                    update_fields["credits_used"] = 0
                else:
                    update_fields["daily_credit_limit"] = 3
                supabase.table("profiles").update(update_fields).eq(
                    "id", user_id
                ).execute()
                profile["tier"] = expected_tier
                profile["daily_credit_limit"] = update_fields["daily_credit_limit"]
                if "credits_used" in update_fields:
                    profile["credits_used"] = update_fields["credits_used"]
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
