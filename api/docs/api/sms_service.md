# SMS Service - Complete Implementation Guide

## Overview

This is a production-ready Amazon SNS SMS service implementation with:

- ✅ Direct SMS to phone numbers (no topic subscription required)
- ✅ Template-based messaging with variable substitution
- ✅ OTP generation and verification with Redis
- ✅ Phone number validation (E.164 format)
- ✅ Message length calculation and optimization
- ✅ Sender ID support (where available)
- ✅ Promotional vs Transactional routing
- ✅ Comprehensive error handling and logging
- ✅ Opt-out management
- ✅ Delivery status tracking
- ✅ Rate limiting and spending controls
- ✅ Cost estimation per message
- ✅ Bulk SMS support

## File Structure

```
src/
├── common/
│   ├── sms_service.py          # Core SNS SMS service
│   └── sms_helpers.py           # High-level helper functions
```

## Configuration

### 1. Environment Variables

Update your `.env` file:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1  # Choose region closest to your customers
```

### 2. SNS SMS Configuration

Set up SNS SMS attributes in AWS Console or programmatically:

```python
from src.common.sms_service import sms_service

# Set account-level SMS preferences
await sms_service.set_sms_attributes({
    "DefaultSMSType": "Transactional",  # or "Promotional"
    "MonthlySpendLimit": "100",  # USD
    "DefaultSenderID": "YourBrand",  # Where supported
    "UsageReportS3Bucket": "your-bucket-name",
})
```

### 3. Move Out of SMS Sandbox

AWS SNS starts in sandbox mode. To send to unverified numbers:

1. Go to AWS SNS Console
2. SMS and mobile push > Text messaging (SMS) > Sandbox destination phone numbers
3. Request production access via AWS Support
4. Provide use case details and compliance information

### 4. Request Sender ID (Optional)

For countries that support Sender ID:

1. Open AWS Support case
2. Request Sender ID registration
3. Provide business details and use case
4. Wait for approval (varies by country)

**Note**: India requires pre-registration with telecom providers. US doesn't support Sender IDs.

## Phone Number Format

All phone numbers must be in E.164 format:

```
+[country_code][number]

Examples:
- India: +919876543210
- US: +12025551234
- UK: +447911123456
```

The service automatically normalizes numbers:
- Removes spaces, hyphens, parentheses
- Adds + prefix if missing
- Defaults to India (+91) if no country code

## Usage Examples

### Example 1: Send Simple SMS

```python
from src.common.sms_service import sms_service

# Send basic SMS
result = await sms_service.send_sms(
    phone_number="+919876543210",
    message="Your order has been confirmed. Thank you for choosing us!"
)

print(f"Message ID: {result['message_id']}")
print(f"Parts: {result['message_parts']}")
print(f"Estimated cost: ${result['estimated_cost']}")
```

### Example 2: Send with Sender ID

```python
# Send with custom sender ID (where supported)
result = await sms_service.send_sms(
    phone_number="+919876543210",
    message="Your OTP is 123456",
    sender_id="YourBrand",
    sms_type=SMSType.TRANSACTIONAL
)
```

### Example 3: Send OTP

```python
from src.common.sms_service import sms_service

# Generate and send OTP
result = await sms_service.send_otp(
    phone_number="+919876543210",
    length=6,
    validity_minutes=10,
    purpose="login"
)

# Verify OTP later
is_valid = await sms_service.verify_otp(
    phone_number="+919876543210",
    otp="123456",
    purpose="login"
)

if is_valid:
    print("OTP verified successfully!")
else:
    print("Invalid or expired OTP")
```

### Example 4: Send Templated SMS

```python
# Using predefined templates
result = await sms_service.send_templated_sms(
    phone_number="+919876543210",
    template_name="order_confirmation",
    variables={
        "order_number": "ORD-2024-001",
        "delivery_time": "30 minutes",
        "track_url": "https://yourapp.com/track/abc123"
    }
)
```

### Example 5: Using SMS Helpers

```python
from src.common.sms_helpers import sms_helpers

# Send verification OTP
await sms_helpers.send_verification_otp(
    phone_number="+919876543210",
    purpose="registration",
    length=6,
    validity_minutes=10
)

# Send order confirmation
await sms_helpers.send_order_confirmation(
    phone_number="+919876543210",
    order_number="ORD-2024-001",
    restaurant_name="Pizza Palace",
    estimated_time="30-40 minutes",
    track_url="https://yourapp.com/track/abc123"
)

# Send delivery assignment
await sms_helpers.send_delivery_assignment(
    phone_number="+919876543210",
    order_number="ORD-2024-001",
    driver_name="Rajesh Kumar",
    driver_phone="+919876543211",
    estimated_time="15 minutes"
)

# Send payment confirmation
await sms_helpers.send_payment_confirmation(
    phone_number="+919876543210",
    order_number="ORD-2024-001",
    amount=549.00,
    payment_method="UPI"
)

# Send to restaurant owner
await sms_helpers.send_restaurant_new_order_alert(
    phone_number="+919876543212",
    order_number="ORD-2024-001",
    items_count=3,
    total_amount=549.00,
    customer_name="John Doe"
)
```

### Example 6: Bulk SMS

```python
# Send to multiple recipients
phone_numbers = [
    "+919876543210",
    "+919876543211",
    "+919876543212",
]

results = await sms_service.send_bulk_sms(
    phone_numbers=phone_numbers,
    message="Flash Sale! 50% off on all pizzas today. Order now!",
    sms_type=SMSType.PROMOTIONAL
)

# Check results
for result in results:
    if result.get("success"):
        print(f"✓ {result['phone_number']}: {result['message_id']}")
    else:
        print(f"✗ {result['phone_number']}: {result['error']}")
```

### Example 7: Promotional Campaign

```python
from src.common.sms_helpers import sms_helpers

customer_phones = [...]  # Your customer list

results = await sms_helpers.send_promotional_message(
    phone_numbers=customer_phones,
    offer_title="Weekend Special",
    offer_details="Get 40% off on orders above ₹500",
    promo_code="WEEKEND40",
    valid_until=datetime(2024, 12, 15)
)

print(f"Campaign sent to {len(customer_phones)} customers")
```

### Example 8: Message Length Optimization

```python
# Long message - will be optimized
long_message = "This is a very long message that exceeds the SMS character limit..."

# Automatically optimize to fit in 1 SMS part
result = await sms_service.send_sms(
    phone_number="+919876543210",
    message=long_message,
    optimize=True,  # Truncate if too long
    max_parts=1      # Maximum 1 SMS part
)

# Or allow multiple parts
result = await sms_service.send_sms(
    phone_number="+919876543210",
    message=long_message,
    optimize=False,  # Don't truncate
    max_parts=3       # Allow up to 3 SMS parts
)
```

## Integration with Your Application

### 1. In Authentication Service

```python
# src/apps/authentication/service.py

from src.common.sms_helpers import sms_helpers

class AuthService:
    async def send_login_otp(self, phone_number: str):
        """Send OTP for phone number login"""
        
        result = await sms_helpers.send_verification_otp(
            phone_number=phone_number,
            purpose="login",
            length=6,
            validity_minutes=10
        )
        
        return {
            "message": "OTP sent successfully",
            "expires_in": 600  # 10 minutes
        }
    
    async def verify_login_otp(self, phone_number: str, otp: str):
        """Verify OTP for login"""
        
        is_valid = await sms_helpers.verify_user_otp(
            phone_number=phone_number,
            otp=otp,
            purpose="login"
        )
        
        if not is_valid:
            raise ValueError("Invalid or expired OTP")
        
        # Create session, generate JWT, etc.
        return {"access_token": "..."}
    
    async def send_password_reset_otp(self, phone_number: str):
        """Send OTP for password reset"""
        
        return await sms_helpers.send_password_reset_otp(
            phone_number=phone_number,
            length=6,
            validity_minutes=15
        )
```

### 2. In Orders Service

```python
# src/apps/orders/service.py

from src.common.sms_helpers import sms_helpers

class OrderService:
    async def create_order(self, order_data: OrderCreate):
        # ... create order logic ...
        
        # Send confirmation SMS to customer
        await sms_helpers.send_order_confirmation(
            phone_number=customer.phone,
            order_number=order.order_number,
            restaurant_name=restaurant.name,
            estimated_time=order.estimated_delivery,
            track_url=f"https://yourapp.com/track/{order.id}"
        )
        
        # Notify restaurant owner
        await sms_helpers.send_restaurant_new_order_alert(
            phone_number=restaurant.owner_phone,
            order_number=order.order_number,
            items_count=len(order.items),
            total_amount=order.total,
            customer_name=customer.name
        )
        
        return order
    
    async def update_order_status(self, order_id: UUID, new_status: str):
        # ... update order logic ...
        
        status_messages = {
            "preparing": "Your order is being prepared",
            "ready": "Your order is ready for pickup",
            "out_for_delivery": "Your order is out for delivery",
            "delivered": "Your order has been delivered"
        }
        
        await sms_helpers.send_order_status_update(
            phone_number=order.customer.phone,
            order_number=order.order_number,
            status=new_status,
            message=status_messages.get(new_status, "Status updated")
        )
```

### 3. In Delivery Service

```python
# src/apps/delivery/service.py

from src.common.sms_helpers import sms_helpers

class DeliveryService:
    async def assign_driver(self, order_id: UUID, driver_id: UUID):
        # ... assignment logic ...
        
        # Notify customer
        await sms_helpers.send_delivery_assignment(
            phone_number=order.customer.phone,
            order_number=order.order_number,
            driver_name=driver.name,
            driver_phone=driver.phone,
            estimated_time="15 minutes"
        )
        
        # Notify driver
        await sms_helpers.send_driver_assignment_notification(
            phone_number=driver.phone,
            order_number=order.order_number,
            pickup_address=order.restaurant.address,
            delivery_address=order.delivery_address,
            customer_phone=order.customer.phone
        )
    
    async def complete_delivery(self, order_id: UUID):
        # ... completion logic ...
        
        await sms_helpers.send_delivery_completed(
            phone_number=order.customer.phone,
            order_number=order.order_number,
            feedback_url=f"https://yourapp.com/feedback/{order.id}"
        )
```

### 4. Celery Task for Async SMS

```python
# tasks/sms_tasks.py

from celery import shared_task
from src.common.sms_helpers import sms_helpers
import asyncio

@shared_task(bind=True, max_retries=3)
def send_order_confirmation_sms_task(self, order_data: dict):
    """
    Celery task to send order confirmation SMS asynchronously
    """
    try:
        asyncio.run(
            sms_helpers.send_order_confirmation(**order_data)
        )
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def send_promotional_campaign_task(campaign_data: dict):
    """
    Send promotional SMS campaign
    """
    phone_numbers = campaign_data['phone_numbers']
    
    asyncio.run(
        sms_helpers.send_promotional_message(
            phone_numbers=phone_numbers,
            offer_title=campaign_data['offer_title'],
            offer_details=campaign_data['offer_details'],
            promo_code=campaign_data.get('promo_code'),
            valid_until=campaign_data.get('valid_until')
        )
    )

# Usage in your service
from tasks.sms_tasks import send_order_confirmation_sms_task

# Send SMS asynchronously
send_order_confirmation_sms_task.delay({
    'phone_number': customer.phone,
    'order_number': order.order_number,
    'restaurant_name': restaurant.name,
    'estimated_time': '30 minutes',
    'track_url': track_url
})
```

## Message Length & Optimization

### GSM-7 Character Set (160 chars/SMS)

Standard characters: A-Z, a-z, 0-9, @, £, $, ¥, common punctuation

**Extended characters** (count as 2):  ^, {, }, \, [, ~], |, €

### Unicode/UCS-2 (70 chars/SMS)

Used when message contains characters outside GSM-7:
- Emojis: 😊, 🍕, 🚗
- Regional characters: ä, ö, ü, ñ, आ, க
- Special symbols: ™, ®, ©

### Multi-part Messages

- GSM-7: 153 chars per part (after first message)
- Unicode: 67 chars per part (after first message)

### Optimization Tips

```python
# Good: Fits in 1 SMS (160 chars)
"Order ORD-001 confirmed! ETA 30 mins. Track: https://app.co/t/abc"

# Bad: Uses Unicode due to emoji (70 chars limit)
"Order confirmed! 🍕 ETA 30 mins"

# Better: Remove emoji
"Order confirmed! ETA 30 mins"

# Good: Use URL shortener for long links
"Order ORD-001. Track: https://bit.ly/abc123"
```

## SMS Types

### Transactional ($0.00645 per message in India)

Use for:
- OTP/verification codes
- Order confirmations
- Delivery updates
- Payment confirmations
- Security alerts
- Password resets

**Higher priority, higher cost, better deliverability**

### Promotional ($0.00258 per message in India)

Use for:
- Marketing campaigns
- Special offers
- Discount codes
- Event notifications
- Newsletters

**Lower cost, may be throttled, requires opt-in**

## Opt-Out Management

AWS SNS automatically handles opt-outs:

```python
# Check if number has opted out
is_opted_out = sms_service.check_opt_out_status("+919876543210")

if is_opted_out:
    print("User has opted out. Cannot send SMS.")
else:
    # Send SMS
    pass

# List all opted-out numbers
opted_out_numbers = await sms_service.list_opted_out_numbers()
print(f"Total opted out: {len(opted_out_numbers)}")
```

Users can opt out by replying "STOP" to any SMS.

## Monitoring & Analytics

### Get SMS Attributes

```python
# Get current SMS settings
attributes = sms_service.get_sms_attributes()

print(f"Default SMS Type: {attributes.get('DefaultSMSType')}")
print(f"Monthly Spend Limit: ${attributes.get('MonthlySpendLimit')}")
print(f"Default Sender ID: {attributes.get('DefaultSenderID')}")
```

### CloudWatch Metrics

Monitor in AWS Console > CloudWatch > Metrics > SNS:

- `NumberOfMessagesPublished`
- `NumberOfNotificationsFailed`
- `SMSSuccessRate`

### Set Up CloudWatch Alarms

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Alarm for high failure rate
cloudwatch.put_metric_alarm(
    AlarmName='SNS-SMS-High-Failure-Rate',
    MetricName='NumberOfNotificationsFailed',
    Namespace='AWS/SNS',
    Statistic='Sum',
    Period=3600,
    EvaluationPeriods=1,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:region:account:topic']
)
```

### Enable Delivery Status Logs

```python
# Configure delivery status logging
sms_service.set_sms_attributes({
    "DeliveryStatusIAMRole": "arn:aws:iam::account:role/SNSSuccessFeedback",
    "DeliveryStatusSuccessSamplingRate": "100"  # Log 100% of success
})
```

## Best Practices

1. **Always use E.164 format** for phone numbers
2. **Validate phone numbers** before sending
3. **Use Transactional type** for critical messages
4. **Keep messages concise** to minimize cost
5. **Implement opt-out handling** (AWS does this automatically)
6. **Set spending limits** to prevent cost overruns
7. **Monitor delivery rates** and failures
8. **Test in sandbox** before production
9. **Handle errors gracefully** with retry logic
10. **Log all SMS operations** for auditing

## Country-Specific Requirements

### India

- **Sender ID**: Requires DLT (Distributed Ledger Technology) registration
- **Templates**: Must register templates with DLT
- **Entity ID**: Required for all commercial SMS
- **Time restrictions**: No promotional SMS 9 PM - 9 AM
- **Registration**: Use TRAI DLT platform

### United States

- **10DLC**: Required for application-to-person (A2P) messaging
- **Sender ID**: Not supported (shows as phone number)
- **Registration**: 15 business days for toll-free numbers
- **Compliance**: Follow TCPA and CAN-SPAM regulations

### Singapore

- **Sender ID**: Requires SSIR registration
- **Registration**: Via AWS Pinpoint console
- **Content**: Subject to review

### China

- **Templates**: Must be pre-approved by AWS Support
- **Registration**: Required for all senders
- **Content**: Subject to strict review

## Troubleshooting

### Common Errors

**Invalid phone number format**
```
ValueError: Invalid phone number format
```
Solution: Ensure number is in E.164 format (+countrycode + number)

**Opted out**
```
ClientError: Phone number has opted out
```
Solution: User replied "STOP". Remove from list or contact via other means.

**Rate limit exceeded**
```
ThrottlingException: Rate exceeded
```
Solution: Implement exponential backoff retry logic

**Spending limit reached**
```
InvalidParameter: Monthly spend limit exceeded
```
Solution: Increase monthly spending limit via AWS Support

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show:
# - Phone number validation
# - Message length calculation
# - SNS API calls
# - Detailed error messages
```

## Cost Optimization

### Tips to Reduce Costs

1. **Use Promotional type** for marketing (50% cheaper)
2. **Optimize message length** to fit in 1 SMS part
3. **Avoid Unicode** characters when possible
4. **Use shortened URLs** for links
5. **Batch messages** during off-peak hours
6. **Remove invalid/inactive** numbers from lists

### Cost Examples (India)

| Scenario | Type | Parts | Cost |
|----------|------|-------|------|
| OTP (6 chars) | Transactional | 1 | $0.00645 |
| Order confirmation (120 chars) | Transactional | 1 | $0.00645 |
| Promotional offer (140 chars) | Promotional | 1 | $0.00258 |
| Long message (300 chars) | Transactional | 2 | $0.01290 |

## Production Checklist

- [ ] Move out of SNS SMS sandbox
- [ ] Set monthly spending limit
- [ ] Configure sender ID (if supported)
- [ ] Set up CloudWatch alarms
- [ ] Enable delivery status logs
- [ ] Implement opt-out handling
- [ ] Test phone number validation
- [ ] Verify OTP generation/verification
- [ ] Test message length optimization
- [ ] Implement error handling & retries
- [ ] Configure rate limiting
- [ ] Set up monitoring dashboard
- [ ] Document country-specific requirements
- [ ] Train team on SMS best practices

## Support

For issues:
- Check AWS SNS Console for delivery logs
- Review CloudWatch metrics
- Monitor opted-out numbers
- Verify phone number format
- Check spending limits