# Stripe Integration Setup Guide

This guide will walk you through setting up Stripe payments for premium purchases in Invoice Australia.

## Prerequisites

- A Stripe account (sign up at [stripe.com](https://stripe.com))
- Python 3.8+ with pip installed
- Your Flask application running

## Step 1: Install Dependencies

```bash
pip install stripe==7.8.0
```

## Step 2: Get Your Stripe API Keys

1. **Log into your Stripe Dashboard** at [dashboard.stripe.com](https://dashboard.stripe.com)

2. **Navigate to Developers > API keys**

3. **Copy your keys:**
   - **Publishable key** (starts with `pk_test_` for test mode)
   - **Secret key** (starts with `sk_test_` for test mode)

4. **For production:**
   - Switch to "Live" mode in the dashboard
   - Use the live keys (start with `pk_live_` and `sk_live_`)

## Step 3: Configure Environment Variables

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your-publishable-key-here
STRIPE_SECRET_KEY=sk_test_your-secret-key-here
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret-here
```

## Step 4: Set Up Webhooks (Required for Production)

Webhooks ensure your application is notified when payments are completed.

### For Development (ngrok method):

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or install via package manager
   ```

2. **Start your Flask app:**
   ```bash
   python run_dev.py
   ```

3. **Expose your local server:**
   ```bash
   ngrok http 5000
   ```

4. **Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

5. **In Stripe Dashboard:**
   - Go to Developers > Webhooks
   - Click "Add endpoint"
   - Enter URL: `https://abc123.ngrok.io/stripe/webhook`
   - Select events: `checkout.session.completed`, `payment_intent.payment_failed`
   - Click "Add endpoint"

6. **Copy the webhook signing secret:**
   - Click on your webhook endpoint
   - Click "Reveal" next to "Signing secret"
   - Copy the `whsec_` value to your `.env` file

### For Production:

1. **Deploy your application** to a server with HTTPS

2. **In Stripe Dashboard:**
   - Go to Developers > Webhooks
   - Click "Add endpoint"
   - Enter URL: `https://yourdomain.com/stripe/webhook`
   - Select events: `checkout.session.completed`, `payment_intent.payment_failed`
   - Click "Add endpoint"

3. **Copy the webhook signing secret** as described above

## Step 5: Test the Integration

### Test Mode (Recommended for Development):

1. **Use test card numbers:**
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Any future date and any 3-digit CVC

2. **Test the flow:**
   - Log in to your app
   - Go to `/premium`
   - Click "Upgrade to Premium"
   - Complete payment with test card
   - Verify user is upgraded to premium

### Test Webhooks Locally:

1. **Install Stripe CLI:**
   ```bash
   # Download from https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe:**
   ```bash
   stripe login
   ```

3. **Forward webhooks to your local server:**
   ```bash
   stripe listen --forward-to localhost:5000/stripe/webhook
   ```

4. **Copy the webhook secret** from the CLI output to your `.env` file

## Step 6: Production Deployment

### Security Checklist:

- [ ] Use live Stripe keys (not test keys)
- [ ] Set up webhook endpoint with HTTPS
- [ ] Verify webhook signatures
- [ ] Handle payment failures gracefully
- [ ] Log all payment events
- [ ] Test with real cards (small amounts)

### Environment Variables for Production:

```bash
STRIPE_PUBLISHABLE_KEY=pk_live_your-live-publishable-key
STRIPE_SECRET_KEY=sk_live_your-live-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-live-webhook-secret
```

## Step 7: Monitoring and Analytics

### Stripe Dashboard Features:

1. **Payments:** Monitor successful and failed payments
2. **Customers:** Track customer information
3. **Disputes:** Handle chargebacks and disputes
4. **Analytics:** View revenue and conversion metrics

### Application Logging:

The application logs all payment events. Check your logs for:
- Checkout session creation
- Payment success/failure
- Webhook processing
- User premium status updates

## Troubleshooting

### Common Issues:

1. **"Invalid API key" error:**
   - Check your `STRIPE_SECRET_KEY` is correct
   - Ensure you're using the right mode (test/live)

2. **Webhook signature verification fails:**
   - Verify `STRIPE_WEBHOOK_SECRET` is correct
   - Check webhook endpoint URL is accessible

3. **Payment succeeds but user not upgraded:**
   - Check webhook is properly configured
   - Verify database connection
   - Check application logs for errors

4. **"No such customer" error:**
   - Ensure customer email is being passed correctly
   - Check Stripe account mode matches your keys

### Debug Mode:

Enable debug logging by adding to your `.env`:

```bash
FLASK_ENV=development
FLASK_DEBUG=1
```

## Support

- **Stripe Documentation:** [stripe.com/docs](https://stripe.com/docs)
- **Stripe Support:** [support.stripe.com](https://support.stripe.com)
- **Application Issues:** Check the application logs and GitHub issues

## Security Notes

- Never commit your Stripe secret keys to version control
- Always use HTTPS in production
- Verify webhook signatures to prevent replay attacks
- Handle sensitive payment data according to PCI compliance
- Regularly rotate your API keys 