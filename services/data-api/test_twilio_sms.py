"""
Test Twilio SMS Notification
This script tests the SMS alert functionality for high-confidence trades
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twilio_notifier import send_high_confidence_alert, TWILIO_ENABLED

# Sample high-confidence recommendation (90%+)
test_recommendation = {
    "symbol": "AAPL",
    "company": "Apple Inc",
    "market": "US",
    "option_type": "CALL",
    "strike_price": 260.0,
    "entry_price": 3.85,
    "expiration_date": "2026-01-16",
    "days_to_expiry": 3,
    "target1": 5.2841,
    "target1_confidence": 0.95,
    "target2": 7.0455,
    "target2_confidence": 0.81,
    "target3": 9.7854,
    "target3_confidence": 0.58,
    "recommendation": "STRONG BUY",
    "overall_confidence": 0.92,  # 92% - triggers SMS!
    "risk_level": "MEDIUM",
    "source": "Real Market Data",
    "open_interest": 45678,
    "volume": 15234
}

if __name__ == "__main__":
    print("=" * 60)
    print("TWILIO SMS NOTIFICATION TEST")
    print("=" * 60)
    print(f"\nTwilio Status: {'✓ ENABLED' if TWILIO_ENABLED else '✗ DISABLED'}")
    print(f"Target Phone: +13462813319")
    print(f"\nTest Trade:")
    print(f"  Symbol: {test_recommendation['symbol']}")
    print(f"  Confidence: {int(test_recommendation['overall_confidence'] * 100)}%")
    print(f"  Entry Price: ${test_recommendation['entry_price']:.2f}")
    print(f"  Target: ${test_recommendation['target1']:.2f}")
    print(f"  Profit/Contract: ${(test_recommendation['target1'] - test_recommendation['entry_price']) * 100:.0f}")
    
    if not TWILIO_ENABLED:
        print("\n⚠ Twilio is not enabled. Check credentials in environment variables.")
        sys.exit(1)
    
    print("\n📱 Sending test SMS notification...")
    result = send_high_confidence_alert(test_recommendation)
    
    if result:
        print("✓ SMS SENT SUCCESSFULLY!")
        print("\nCheck your phone (+13462813319) for the alert.")
        print("\nNote: Duplicate alerts for the same trade are automatically prevented.")
    else:
        print("✗ Failed to send SMS. Check logs for details.")
    
    print("=" * 60)
