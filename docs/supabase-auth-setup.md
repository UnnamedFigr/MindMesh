# Supabase Auth Configuration Guide

To ensure authentication works correctly in production, the following manual steps must be completed in your Supabase Dashboard:

## 1. Authentication Providers
Navigate to **Authentication > Providers**.

*   **Email Setup:** Ensure the "Enable Email provider" toggle is active.
*   **Google OAuth (Optional but Recommended):**
    *   Enable the Google provider.
    *   You will need to create credentials in the Google Cloud Console (Client ID and Client Secret).
    *   Set the authorized redirect URI in Google Cloud to match your Supabase project URL + `/auth/v1/callback` (e.g., `https://[PROJECT_REF].supabase.co/auth/v1/callback`).

## 2. URL Configuration
Navigate to **Authentication > URL Configuration**.

*   **Site URL:** Set this to your primary production frontend URL (e.g., `https://mindmesh.app`).
*   **Redirect URLs:** Add any other allowed redirect URLs, such as your localhost testing port and Vercel preview URLs (e.g., `http://localhost:3000/**`, `https://*-your-team.vercel.app/**`). This is critical for the magic link and OAuth callbacks to work securely.

## 3. Email Templates
Navigate to **Authentication > Email Templates**.

*   Customize the templates for "Confirm Signup", "Invite User", "Magic Link", and "Reset Password" to match MindMesh's branding.
*   **Crucial:** Ensure the links in the templates use the `{{ .ConfirmationURL }}` variable so users are routed correctly through your Next.js application's auth callback handler (usually `/auth/callback`).

## 4. SMTP Settings (Required for Production)
Navigate to **Project Settings > Email**.

*   By default, Supabase uses a shared SMTP server with strict limits (rate limits and deliverability issues).
*   **Actionable Step:** Configure a custom SMTP provider (like Resend, SendGrid, or AWS SES) to ensure your auth emails (magic links, confirmations) reliably reach the users' inboxes.

## 5. Security & Rate Limits
Navigate to **Authentication > Rate Limits**.

*   Review and adjust the rate limits as needed (e.g., Signups per hour, Magic link requests per hour) to prevent abuse while accommodating your expected user volume.
