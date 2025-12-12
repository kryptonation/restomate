# Email Service - Complete Implementation Guide

## Overview

This is a production-ready Amazon SES email service implementation with:

- ✅ Jinja2 template rendering with autoescaping
- ✅ Multiple attachments support (PDF, images, CSV, etc.)
- ✅ Inline images with CID references
- ✅ HTML and plain text multipart emails
- ✅ Comprehensive error handling and logging
- ✅ AWS SES best practices compliance
- ✅ Email validation and sanitization
- ✅ Configuration set support for analytics
- ✅ Pre-built helper functions for common scenarios

## File Structure

```
src/
├── common/
│   ├── email_service.py          # Core SES service
│   └── email_helpers.py           # High-level helper functions
├── templates/
│   └── email/
│       ├── base.html              # Base email template
│       ├── welcome.subject.txt    # Welcome email subject
│       ├── welcome.html           # Welcome email HTML
│       ├── welcome.txt            # Welcome email plain text
│       ├── order_confirmation.subject.txt
│       ├── order_confirmation.html
│       ├── order_confirmation.txt
│       ├── password_reset.subject.txt
│       ├── password_reset.html
│       ├── invoice.subject.txt
│       ├── invoice.html
│       └── ... (other templates)
```

## Configuration

### 1. Environment Variables

Update your `.env` file:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1

# Email Configuration
EMAIL_FROM=noreply@yourdomain.com
```

### 2. Verify SES Identity

Before sending emails, verify your domain or email addresses in AWS SES:

```python
from src.common.email_service import email_service

# Verify email address (for testing/sandbox)
email_service.verify_email_identity("[email protected]")

# For production, verify domain in AWS SES Console:
# 1. Go to AWS SES Console
# 2. Verified Identities > Create Identity
# 3. Choose Domain
# 4. Add DNS records (DKIM, SPF, DMARC)
```

### 3. Request Production Access

AWS SES starts in sandbox mode. Request production access:

1. Go to AWS SES Console
2. Account Dashboard > Request production access
3. Provide use case details
4. Implement bounce/complaint handling
5. Add unsubscribe mechanism

## Usage Examples

### Example 1: Send Simple Email

```python
from src.common.email_service import email_service

# Send simple HTML email
result = await email_service.send_email(
    to_addresses="[email protected]",
    subject="Welcome to Our Platform",
    html_body="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
    text_body="Welcome! Thanks for signing up."
)

print(f"Message ID: {result['message_id']}")
```

### Example 2: Send Email with Attachments

```python
from src.common.email_service import email_service, EmailAttachment

# Create attachment from file
attachment = EmailAttachment.from_file(
    filepath="path/to/invoice.pdf",
    filename="invoice_12345.pdf"
)

# Send email with attachment
result = await email_service.send_email(
    to_addresses="[email protected]",
    subject="Your Invoice",
    html_body="<p>Please find your invoice attached.</p>",
    attachments=[attachment]
)
```

### Example 3: Send Email with Inline Images

```python
from src.common.email_service import email_service, EmailAttachment

# Create inline image attachment
logo = EmailAttachment.from_file(
    filepath="static/images/logo.png",
    filename="logo.png",
    disposition="inline",
    content_id="company-logo"
)

# Reference in HTML using cid:
html_body = """
<html>
<body>
    <img src="cid:company-logo" alt="Company Logo" width="200"/>
    <h1>Welcome to Our Platform</h1>
</body>
</html>
"""

result = await email_service.send_email(
    to_addresses="[email protected]",
    subject="Welcome",
    html_body=html_body,
    attachments=[logo]
)
```

### Example 4: Send Templated Email

```python
from src.common.email_service import email_service

# Send using Jinja2 template
result = await email_service.send_templated_email(
    to_addresses="[email protected]",
    template_name="welcome",  # Looks for welcome.html, welcome.txt, welcome.subject.txt
    context={
        "user_name": "John Doe",
        "user_role": "Restaurant Owner",
        "verification_url": "https://yourapp.com/verify?token=abc123",
    }
)
```

### Example 5: Using Email Helpers

```python
from src.common.email_helpers import email_helpers

# Send welcome email
await email_helpers.send_welcome_email(
    user_email="[email protected]",
    user_name="John Doe",
    user_role="customer",
    verification_url="https://yourapp.com/verify?token=abc123"
)

# Send order confirmation
await email_helpers.send_order_confirmation(
    customer_email="[email protected]",
    customer_name="John Doe",
    order_id=uuid.uuid4(),
    order_number="ORD-2024-001",
    order_items=[
        {"name": "Margherita Pizza", "quantity": 2, "price": 12.99},
        {"name": "Caesar Salad", "quantity": 1, "price": 8.99}
    ],
    order_total=34.97,
    delivery_address="123 Main St, Chennai",
    estimated_delivery_time="30-40 minutes",
    restaurant_name="Pizza Palace",
    restaurant_phone="+91 98765 43210"
)

# Send invoice with PDF
invoice_pdf = generate_invoice_pdf()  # Your PDF generation function
await email_helpers.send_invoice(
    customer_email="[email protected]",
    customer_name="John Doe",
    invoice_number="INV-2024-001",
    invoice_date=datetime.now(),
    invoice_amount=34.97,
    order_items=[...],
    tax_amount=3.15,
    delivery_fee=2.99,
    discount_amount=5.00,
    pdf_attachment=invoice_pdf
)

# Send password reset
await email_helpers.send_password_reset(
    user_email="[email protected]",
    user_name="John Doe",
    reset_token="abc123xyz",
    expires_at=datetime.now() + timedelta(hours=1)
)
```

### Example 6: Batch Emails

```python
from src.common.email_service import email_service

# Send to multiple recipients (max 50 per email)
result = await email_service.send_email(
    to_addresses=["[email protected]", "[email protected]"],
    cc_addresses=["[email protected]"],
    bcc_addresses=["[email protected]"],
    subject="Weekly Report",
    html_body="<p>Your weekly report is ready.</p>"
)

# For bulk emails (1000+ recipients), use loops
recipients = ["user1@...", "user2@...", ...]  # Your recipient list
batch_size = 50

for i in range(0, len(recipients), batch_size):
    batch = recipients[i:i + batch_size]
    try:
        await email_service.send_email(
            to_addresses=batch,
            subject="Monthly Newsletter",
            html_body=newsletter_html
        )
    except Exception as e:
        logger.error(f"Batch {i} failed: {e}")
```

### Example 7: Custom Headers and Reply-To

```python
result = await email_service.send_email(
    to_addresses="[email protected]",
    subject="Order Support",
    html_body="<p>How can we help?</p>",
    reply_to="[email protected]",
    custom_headers={
        "X-Priority": "1",
        "X-Order-ID": "ORD-12345",
        "X-Customer-ID": "CUST-67890"
    }
)
```

## Template Examples

### welcome.subject.txt
```
Welcome to {{ company_name }}, {{ user_name }}!
```

### welcome.html
```html
{% extends "base.html" %}

{% block content %}
<h2>Welcome, {{ user_name }}!</h2>

<p>We're excited to have you as a {{ user_role }} on our platform.</p>

<div class="info-box">
    <p>Your account has been created successfully. To get started, please verify your email address.</p>
</div>

{% if verification_url %}
<div class="button-wrapper">
    <a href="{{ verification_url }}" class="button button-primary">Verify Email Address</a>
</div>
{% endif %}

<h3>What's Next?</h3>
<ul>
    <li>Complete your profile</li>
    <li>Explore available restaurants</li>
    <li>Place your first order</li>
</ul>

<p>If you have any questions, feel free to reach out to our support team.</p>
{% endblock %}
```

### order_confirmation.subject.txt
```
Order Confirmation - {{ order_number }}
```

### order_confirmation.html
```html
{% extends "base.html" %}

{% block content %}
<h2>Order Confirmed!</h2>

<p>Hi {{ customer_name }},</p>

<p>Thank you for your order. We've received it and {{ restaurant_name }} is preparing your food.</p>

<div class="success-box">
    <p><strong>Order Number:</strong> {{ order_number }}</p>
    <p><strong>Estimated Delivery:</strong> {{ estimated_delivery_time }}</p>
</div>

<h3>Order Details</h3>

<table class="details-table">
    <thead>
        <tr>
            <th>Item</th>
            <th>Quantity</th>
            <th>Price</th>
        </tr>
    </thead>
    <tbody>
        {% for item in order_items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>{{ item.quantity }}</td>
            <td>{{ item.price|currency }}</td>
        </tr>
        {% endfor %}
        <tr class="total-row">
            <td colspan="2"><strong>Total</strong></td>
            <td><strong>{{ order_total|currency }}</strong></td>
        </tr>
    </tbody>
</table>

<div class="info-box">
    <p><strong>Delivery Address:</strong><br>{{ delivery_address }}</p>
</div>

<div class="button-wrapper">
    <a href="{{ track_order_url }}" class="button button-primary">Track Your Order</a>
</div>

<h3>Restaurant Contact</h3>
<p>
    <strong>{{ restaurant_name }}</strong><br>
    Phone: {{ restaurant_phone }}
</p>
{% endblock %}
```

## Integration with Your Application

### 1. In Authentication Service

```python
# src/apps/authentication/service.py

from src.common.email_helpers import email_helpers

class AuthService:
    async def register_user(self, user_data: UserCreate):
        # ... create user logic ...
        
        # Send welcome email
        try:
            await email_helpers.send_welcome_email(
                user_email=user.email,
                user_name=user.full_name,
                user_role=user.role,
                verification_url=f"https://yourapp.com/verify?token={token}"
            )
        except Exception as e:
            logger.error("Failed to send welcome email", error=str(e))
            # Don't fail registration if email fails
        
        return user
    
    async def request_password_reset(self, email: str):
        # ... generate reset token ...
        
        await email_helpers.send_password_reset(
            user_email=email,
            user_name=user.full_name,
            reset_token=token,
            expires_at=expires_at
        )
```

### 2. In Orders Service

```python
# src/apps/orders/service.py

from src.common.email_helpers import email_helpers

class OrderService:
    async def create_order(self, order_data: OrderCreate):
        # ... create order logic ...
        
        # Send confirmation email
        await email_helpers.send_order_confirmation(
            customer_email=customer.email,
            customer_name=customer.full_name,
            order_id=order.id,
            order_number=order.order_number,
            order_items=order.items,
            order_total=order.total,
            delivery_address=order.delivery_address,
            estimated_delivery_time=order.estimated_delivery,
            restaurant_name=restaurant.name,
            restaurant_phone=restaurant.phone
        )
        
        return order
    
    async def update_order_status(self, order_id: UUID, new_status: str):
        # ... update order logic ...
        
        await email_helpers.send_order_status_update(
            customer_email=order.customer.email,
            customer_name=order.customer.full_name,
            order_number=order.order_number,
            old_status=order.status,
            new_status=new_status,
            status_message=self._get_status_message(new_status),
            tracking_url=f"https://yourapp.com/orders/{order_id}"
        )
```

### 3. Celery Task for Async Email Sending

```python
# tasks/email_tasks.py

from celery import shared_task
from src.common.email_helpers import email_helpers

@shared_task(bind=True, max_retries=3)
def send_order_confirmation_task(self, order_data: dict):
    """
    Celery task to send order confirmation email asynchronously
    """
    try:
        asyncio.run(
            email_helpers.send_order_confirmation(**order_data)
        )
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def send_weekly_reports_task(self):
    """
    Celery task to send weekly reports to all restaurants
    """
    # ... fetch restaurant data and generate reports ...
    
    for restaurant in restaurants:
        try:
            asyncio.run(
                email_helpers.send_weekly_report(
                    recipient_email=restaurant.email,
                    recipient_name=restaurant.owner_name,
                    report_period=report_period,
                    total_orders=stats.total_orders,
                    total_revenue=stats.total_revenue,
                    total_customers=stats.total_customers,
                    top_items=stats.top_items,
                    report_pdf=generate_pdf(stats)
                )
            )
        except Exception as e:
            logger.error(f"Failed to send report to {restaurant.id}", error=str(e))
```

## Monitoring and Analytics

### Check SES Quota

```python
from src.common.email_service import email_service

# Get sending quota
quota = email_service.get_send_quota()
print(f"Daily limit: {quota['max_24_hour_send']}")
print(f"Sent today: {quota['sent_last_24_hours']}")
print(f"Remaining: {quota['remaining']}")

# Get statistics
stats = email_service.get_send_statistics()
for data_point in stats:
    print(f"Bounces: {data_point['Bounces']}")
    print(f"Complaints: {data_point['Complaints']}")
    print(f"Delivery Attempts: {data_point['DeliveryAttempts']}")
```

### Set up CloudWatch Alarms

```python
# Monitor bounce rate, complaint rate, and delivery metrics
# Set up in AWS Console or using boto3:

import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_alarm(
    AlarmName='SES-High-Bounce-Rate',
    MetricName='Reputation.BounceRate',
    Namespace='AWS/SES',
    Statistic='Average',
    Period=3600,
    EvaluationPeriods=1,
    Threshold=0.05,  # 5% bounce rate
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:region:account:topic']
)
```

## Best Practices

1. **Always include unsubscribe links** for marketing emails (required by law)
2. **Implement bounce and complaint handling** via SNS notifications
3. **Keep spam complaint rate < 0.1%** (AWS suspends at 0.5%)
4. **Use configuration sets** for tracking opens, clicks, bounces
5. **Warm up dedicated IPs** gradually if using dedicated IPs
6. **Authenticate emails** with SPF, DKIM, and DMARC
7. **Test emails thoroughly** before sending to customers
8. **Monitor sending metrics** regularly
9. **Use templates** for consistency and maintainability
10. **Implement retry logic** for transient failures

## Troubleshooting

### Email Not Sending

```python
# Check if sender email is verified
from src.common.email_service import email_service

try:
    result = await email_service.send_email(...)
    print(f"Success: {result}")
except ValueError as e:
    print(f"Validation error: {e}")
except ClientError as e:
    print(f"AWS error: {e.response['Error']['Code']}")
    print(f"Message: {e.response['Error']['Message']}")
```

### Common Errors

- **MessageRejected**: Email content rejected (spam-like, malformed)
- **MailFromDomainNotVerifiedException**: Sender not verified
- **AccountSendingPausedException**: Account suspended (high bounce/complaint rate)
- **ConfigurationSetDoesNotExist**: Invalid configuration set
- **DailyQuotaExceeded**: Exceeded daily sending limit

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed logs including:
# - Template rendering
# - MIME message construction
# - SES API calls
# - Attachment processing
```

## Production Checklist

- [ ] Domain verified in SES with DKIM
- [ ] SPF record added to DNS
- [ ] DMARC policy configured
- [ ] Production access granted
- [ ] Bounce/complaint handling configured
- [ ] CloudWatch alarms set up
- [ ] Unsubscribe mechanism implemented
- [ ] Email templates tested
- [ ] Sending quotas monitored
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Retry logic in place
- [ ] Template directory structure created
- [ ] Base templates deployed

## Support

For issues or questions:
- Check AWS SES Console for detailed error messages
- Review CloudWatch logs for SES events
- Monitor bounce and complaint rates
- Check sending statistics and quotas