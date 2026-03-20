# ── MindMesh Deployment Guide ──────────────────────────────────
#
# Architecture:
#   Frontend  →  Vercel      (Next.js, auto-deployed from Git)
#   Backend   →  Render      (Docker, render.yaml Blueprint)
#   Database  →  Supabase    (already running)
#   Payments  →  Stripe      (webhooks)
#
# ────────────────────────────────────────────────────────────────

## 1. Prerequisites

- GitHub repo pushed (dev or main branch)
- Supabase project running (already: qkjhqwsecfuhvaopxslh)
- Stripe account with product created (already: price_1TChScPQujtWPrdKOgaWRljr)
- Vercel account (https://vercel.com)
- Render account (https://render.com)


## 2. Deploy Backend to Render

1. Go to https://dashboard.render.com → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` in the root
4. Set environment variables in the Render dashboard:

   ```
   ENVIRONMENT=production
   SUPABASE_URL=https://qkjhqwsecfuhvaopxslh.supabase.co
   SUPABASE_SERVICE_KEY=<your-supabase-service-role-key>
   SUPABASE_JWT_SECRET=<your-supabase-jwt-secret>
   OPENAI_API_KEY=<your-openai-key>
   GROQ_API_KEY=<your-groq-key>
   STRIPE_SECRET_KEY=<your-stripe-secret-key>  (use sk_live_* for production)
   STRIPE_WEBHOOK_SECRET=<from-step-5>
   ALLOWED_ORIGINS=https://your-app.vercel.app
   YOUTUBE_API_KEY=<optional>
   ```

5. Click **Apply** → Render builds the Docker image and deploys
6. Note your backend URL: `https://mindmesh-api.onrender.com`


## 3. Deploy Frontend to Vercel

1. Go to https://vercel.com → **Add New Project**
2. Import your GitHub repo
3. Set these settings:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `pnpm build`
   - **Install Command:** `pnpm install --frozen-lockfile`

4. Set environment variables:

   ```
   NEXT_PUBLIC_SUPABASE_URL=https://qkjhqwsecfuhvaopxslh.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
   NEXT_PUBLIC_API_URL=https://mindmesh-api.onrender.com
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>  (use pk_live_* for production)
   NEXT_PUBLIC_STRIPE_PRO_PRICE_ID=price_1TChScPQujtWPrdKOgaWRljr
   ```

5. Click **Deploy**
6. Note your frontend URL: `https://your-app.vercel.app`


## 4. Post-Deploy Configuration

### 4a. Update CORS on Render
Set `ALLOWED_ORIGINS` to your actual Vercel URL:
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### 4b. Configure Supabase Auth Redirect URLs
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Set **Site URL** to: `https://your-app.vercel.app`
3. Add to **Redirect URLs**:
   - `https://your-app.vercel.app/auth/callback`
   - `http://localhost:3000/auth/callback` (keep for local dev)

### 4c. Set Up Stripe Webhook (Production)
1. Go to https://dashboard.stripe.com → Developers → Webhooks
2. Click **Add endpoint**
3. Set URL: `https://mindmesh-api.onrender.com/api/webhooks/stripe`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (`whsec_...`)
6. Set it as `STRIPE_WEBHOOK_SECRET` in Render dashboard

### 4d. Switch Stripe to Live Mode (when ready)
1. In Stripe Dashboard, toggle to **Live mode**
2. Create the same product/price in live mode
3. Update environment variables:
   - Render: `STRIPE_SECRET_KEY` → `sk_live_...`
   - Render: `STRIPE_WEBHOOK_SECRET` → new live webhook secret
   - Vercel: `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` → `pk_live_...`
   - Vercel: `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID` → new live price ID


## 5. Verify Deployment

1. **Health check:** `curl https://mindmesh-api.onrender.com/health`
2. **Frontend:** Visit `https://your-app.vercel.app`
3. **Auth flow:** Sign up → confirm email → redirect to dashboard
4. **Guide generation:** Submit a YouTube URL → wait for guide
5. **Stripe:** Test checkout flow with Stripe test card `4242 4242 4242 4242`


## 6. Custom Domain (Optional)

### Vercel
1. Vercel Dashboard → Settings → Domains → Add domain
2. Add DNS CNAME record: `your-domain.com` → `cname.vercel-dns.com`

### Render
1. Render Dashboard → Your service → Settings → Custom Domains
2. Add DNS CNAME record: `api.your-domain.com` → `your-service.onrender.com`
3. Update `ALLOWED_ORIGINS` on Render and `NEXT_PUBLIC_API_URL` on Vercel


## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors | Check `ALLOWED_ORIGINS` matches your Vercel URL exactly (no trailing slash) |
| Auth redirect fails | Verify Supabase redirect URLs include your production callback URL |
| Stripe webhooks 400 | Verify `STRIPE_WEBHOOK_SECRET` matches the endpoint's signing secret |
| Backend cold starts | Render free tier sleeps after 15 min inactivity — upgrade to Starter ($7/mo) |
| Build fails on Vercel | Ensure Root Directory is set to `frontend` |
