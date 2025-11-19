# Mailjet Email Configuration

This project uses Mailjet for sending transactional emails.

## Setup Instructions

### 1. Environment Variables

Set the following environment variables in your `.env` file or production environment:

```bash
MAILJET_API_KEY=your_api_key_here
MAILJET_SECRET_KEY=your_secret_key_here
MAILJET_FROM_EMAIL=no-reply@thenewafricagroup.com
```

**Current Credentials:**
- Email: `no-reply@thenewafricagroup.com`
- API Key: Stored in environment variables
- Secret Key: Stored in environment variables

### 2. Django Settings

The following settings are configured in `myproject/settings.py`:

```python
# Email Configuration - Mailjet
EMAIL_BACKEND = 'django_mailjet.backends.MailjetBackend'
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', '')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '')
MAILJET_FROM_EMAIL = os.environ.get('MAILJET_FROM_EMAIL', 'no-reply@thenewafricagroup.com')
MAILJET_FROM_NAME = 'The New Africa Group'

# Django email settings (backup)
EMAIL_HOST = 'in-v3.mailjet.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('MAILJET_API_KEY', '')
EMAIL_HOST_PASSWORD = os.environ.get('MAILJET_SECRET_KEY', '')
DEFAULT_FROM_EMAIL = MAILJET_FROM_EMAIL
SERVER_EMAIL = MAILJET_FROM_EMAIL
```

### 3. Using the Email Service

#### Simple Email
```python
from utils.mailjet_service import send_email

send_email(
    to_email='user@example.com',
    to_name='John Doe',
    subject='Welcome!',
    html_content='<h1>Hello John!</h1>',
    text_content='Hello John!'
)
```

#### With Templates
```python
from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template

html = welcome_email_template(
    user_name='John Doe',
    activation_url='https://example.com/activate/token123'
)

send_email(
    to_email='user@example.com',
    to_name='John Doe',
    subject='Activate Your Account',
    html_content=html
)
```

#### Batch Emails
```python
from utils.mailjet_service import send_batch_emails

recipients = [
    {'email': 'user1@example.com', 'name': 'User One'},
    {'email': 'user2@example.com', 'name': 'User Two'},
]

send_batch_emails(
    recipients=recipients,
    subject='Newsletter',
    html_content='<h1>Latest Updates</h1>...'
)
```

### 4. Email Templates

Available templates in `utils/email_templates.py`:

- **`welcome_email_template()`** - New user welcome email
- **`password_reset_email_template()`** - Password reset instructions
- **`notification_email_template()`** - Generic notification email

### 5. Integration Examples

#### User Registration
```python
from django.contrib.auth.models import User
from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template

def register_user(email, name):
    user = User.objects.create_user(username=email, email=email)
    activation_url = f"https://example.com/activate/{user.id}"
    
    html = welcome_email_template(name, activation_url)
    send_email(
        to_email=email,
        to_name=name,
        subject='Welcome to The New Africa Group',
        html_content=html
    )
```

#### Password Reset
```python
from utils.mailjet_service import send_email
from utils.email_templates import password_reset_email_template

def send_password_reset(user):
    reset_url = f"https://example.com/reset/{user.id}"
    
    html = password_reset_email_template(
        user_name=user.get_full_name() or user.username,
        reset_url=reset_url
    )
    
    send_email(
        to_email=user.email,
        to_name=user.get_full_name(),
        subject='Reset Your Password',
        html_content=html
    )
```

### 6. Testing

To test email sending in development:

```python
from utils.mailjet_service import mailjet_service

# Test connection
result = mailjet_service.send_email(
    to_email='test@example.com',
    subject='Test Email',
    html_content='<p>This is a test</p>',
    text_content='This is a test'
)

print(f"Email sent: {result}")
```

### 7. Monitoring & Logs

Check Django logs for email sending:

```python
import logging

logger = logging.getLogger('utils.mailjet_service')
```

Mailjet provides:
- Delivery status tracking
- Open/click tracking
- Bounce management
- Spam reporting

Access these features in the Mailjet dashboard.

### 8. Production Deployment

For PythonAnywhere or production:

1. Set environment variables in your hosting provider's settings
2. Ensure `requests` library is installed (included in requirements.txt)
3. Test email sending after deployment

### 9. Troubleshooting

**Issue: "Mailjet credentials not configured"**
- Ensure `MAILJET_API_KEY` and `MAILJET_SECRET_KEY` are set in environment

**Issue: Email not sending**
- Check Mailjet API credentials are correct
- Verify email address is valid
- Check Django logs for error messages
- Ensure from email is verified in Mailjet account

**Issue: Emails going to spam**
- Add SPF and DKIM records to your domain DNS
- Configure reply-to addresses
- Use clear subject lines
- Include unsubscribe links for newsletters

### References

- [Mailjet API Documentation](https://dev.mailjet.com/)
- [Mailjet Python SDK](https://github.com/mailjet/mailjet-apiv3-python)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
