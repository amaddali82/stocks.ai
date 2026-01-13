"""
Twilio SMS Notification Service
Sends SMS alerts for high-confidence trading recommendations
"""

import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+18447461097')  # Your Twilio number
NOTIFY_PHONE_NUMBER = '+13462813319'  # Your phone number

# Initialize Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    TWILIO_ENABLED = True
    logger.info("✓ Twilio SMS notifications enabled")
except Exception as e:
    TWILIO_ENABLED = False
    logger.warning(f"⚠ Twilio not configured: {e}")

# Track sent notifications to avoid duplicates
sent_notifications = set()

def send_high_confidence_alert(recommendation: dict):
    """Send SMS alert for high-confidence recommendation (>= 90%)"""
    if not TWILIO_ENABLED:
        logger.warning("Twilio not enabled, skipping SMS notification")
        return False
    
    try:
        confidence = recommendation.get('overall_confidence', 0)
        
        # Only send for 90%+ confidence
        if confidence < 0.90:
            return False
        
        # Create unique key to prevent duplicate notifications
        notification_key = f"{recommendation['symbol']}_{recommendation['strike_price']}_{recommendation['expiration_date']}"
        
        if notification_key in sent_notifications:
            logger.debug(f"Notification already sent for {notification_key}")
            return False
        
        # Calculate profit potential
        entry_price = recommendation.get('entry_price', 0)
        target1 = recommendation.get('target1', 0)
        profit_per_contract = (target1 - entry_price) * 100
        capital_required = entry_price * 100
        profit_percent = ((target1 - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Format SMS message
        message = f"""
🎯 HIGH CONFIDENCE TRADE ALERT!

Symbol: {recommendation['symbol']}
Confidence: {int(confidence * 100)}%
Type: {recommendation['option_type']}
Strike: ${recommendation['strike_price']:.2f}

💰 PROFIT POTENTIAL:
Entry: ${entry_price:.2f}
Target: ${target1:.2f}
Profit: ${profit_per_contract:.0f} per contract
Return: +{profit_percent:.0f}%

📊 DETAILS:
Capital Needed: ${capital_required:.0f}
Expires: {recommendation['expiration_date']}
Days Left: {recommendation['days_to_expiry']}

Risk: {recommendation['risk_level']}
Source: {recommendation.get('source', 'Verified')}

🚀 Act fast! High-confidence opportunities don't last.
        """.strip()
        
        # Send SMS via Twilio
        twilio_message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=NOTIFY_PHONE_NUMBER
        )
        
        # Mark as sent
        sent_notifications.add(notification_key)
        
        logger.info(f"✓ SMS sent for {recommendation['symbol']} (Confidence: {int(confidence * 100)}%) - SID: {twilio_message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {e}")
        return False

def check_and_notify_high_confidence(predictions: list):
    """Check all predictions and send SMS for those with >= 90% confidence"""
    if not predictions:
        return 0
    
    notifications_sent = 0
    for prediction in predictions:
        confidence = prediction.get('overall_confidence', 0)
        if confidence >= 0.90:
            if send_high_confidence_alert(prediction):
                notifications_sent += 1
    
    if notifications_sent > 0:
        logger.info(f"📱 Sent {notifications_sent} SMS notification(s) for high-confidence trades")
    
    return notifications_sent

def clear_notification_cache():
    """Clear the notification cache (call this periodically, e.g., daily)"""
    global sent_notifications
    count = len(sent_notifications)
    sent_notifications.clear()
    logger.info(f"Cleared {count} notification(s) from cache")
    return count
