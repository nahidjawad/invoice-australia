"""
Stripe Integration for Premium Purchases
Handles payment processing and webhook events
"""

import stripe
from flask import current_app, request, session
from models import User
from extensions import db
import logging

logger = logging.getLogger(__name__)

def init_stripe():
    """Initialize Stripe with the secret key"""
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY is not set in configuration")
    except RuntimeError:
        # current_app is not available outside of Flask context
        import os
        from dotenv import load_dotenv
        load_dotenv()
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY is not set in environment variables")

def create_checkout_session(user_email, user_id):
    """
    Create a Stripe checkout session for premium purchase
    
    Args:
        user_email (str): User's email address
        user_id (int): User's database ID
    
    Returns:
        stripe.checkout.Session: Created checkout session
    """
    try:
        init_stripe()
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aud',
                    'product_data': {
                        'name': 'Invoice Australia Premium',
                        'description': 'Unlimited invoices, email history, and premium features',
                    },
                    'unit_amount': 1999,  # $19.99 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'stripe/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'premium',
            customer_email=user_email,
            metadata={
                'user_id': str(user_id),
                'user_email': user_email
            }
        )
        
        logger.info(f"Created checkout session {checkout_session.id} for user {user_email}")
        return checkout_session
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise

def handle_webhook_event(payload, sig_header):
    """
    Handle Stripe webhook events
    
    Args:
        payload (bytes): Raw webhook payload
        sig_header (str): Stripe signature header
    
    Returns:
        bool: True if webhook was processed successfully
    """
    try:
        init_stripe()
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
        
        logger.info(f"Received webhook event: {event['type']}")
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session_data = event['data']['object']
            handle_payment_success(session_data)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            handle_payment_failure(payment_intent)
        
        return True
        
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return False
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return False

def handle_payment_success(session_data):
    """
    Handle successful payment completion
    
    Args:
        session_data (dict): Stripe session data
    """
    try:
        user_id = int(session_data['metadata']['user_id'])
        user_email = session_data['metadata']['user_email']
        
        # Update user to premium
        user = User.query.get(user_id)
        if user:
            user.is_premium = True
            db.session.commit()
            
            logger.info(f"User {user_email} upgraded to premium")
        else:
            logger.error(f"User with ID {user_id} not found")
            
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")

def handle_payment_failure(payment_intent):
    """
    Handle payment failure
    
    Args:
        payment_intent (dict): Stripe payment intent data
    """
    try:
        logger.warning(f"Payment failed for payment intent: {payment_intent['id']}")
        # You could send an email to the user here
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")

def get_payment_status(session_id):
    """
    Get payment status for a checkout session
    
    Args:
        session_id (str): Stripe checkout session ID
    
    Returns:
        dict: Payment status information
    """
    try:
        init_stripe()
        session_data = stripe.checkout.Session.retrieve(session_id)
        
        return {
            'status': session_data.payment_status,
            'amount_total': session_data.amount_total,
            'currency': session_data.currency,
            'customer_email': session_data.customer_email
        }
        
    except Exception as e:
        logger.error(f"Error retrieving payment status: {str(e)}")
        return None 