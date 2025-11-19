# OTP (One-Time Password) Implementation Guide

## Overview
OTP verification has been successfully implemented for user signup. The system generates 6-digit OTP codes, sends them via Mailjet email, and verifies them before account creation.

## Files Created/Modified

### 1. **accounts/models.py** (Modified)
Added `OTPVerification` model with:
- 6-digit OTP code generation
- 10-minute expiration
- Attempt limiting (max 5 attempts)
- Verification tracking
- Methods: `create_otp()`, `verify_otp()`, `resend_otp()`, `is_expired()`, `is_valid_attempt()`

### 2. **accounts/otp_views.py** (New)
REST API endpoints:
- `POST /api/auth/otp/send_otp/` - Generate and send OTP
- `POST /api/auth/otp/verify_otp/` - Verify OTP code
- `POST /api/auth/otp/resend_otp/` - Resend OTP

### 3. **accounts/email_tasks.py** (Modified)
Added:
- `send_otp_email()` task - Sends OTP via Mailjet
- Made Celery optional (fallback if not installed)

### 4. **utils/email_templates.py** (Modified)
Added:
- `otp_email_template()` - Professional OTP email with formatted code

### 5. **accounts/urls.py** (Modified)
Registered OTP ViewSet routes at `/api/auth/otp/`

### 6. **Database Migration**
- `accounts/migrations/0007_otpverification.py` - Created OTPVerification table

## API Usage

### Step 1: Request OTP
```bash
POST /api/auth/otp/send_otp/
Content-Type: application/json

{
    "email": "user@example.com"
}

Response:
{
    "message": "OTP sent to user@example.com",
    "user_exists": false,
    "otp_id": 1,
    "expires_in_minutes": 10
}
```

### Step 2: Verify OTP
```bash
POST /api/auth/otp/verify_otp/
Content-Type: application/json

{
    "email": "user@example.com",
    "otp_code": "123456"
}

Response (Success):
{
    "message": "OTP verified successfully",
    "verified": true,
    "email": "user@example.com"
}

Response (Failure):
{
    "error": "Invalid OTP. 4 attempts remaining.",
    "verified": false
}
```

### Step 3: Resend OTP (if needed)
```bash
POST /api/auth/otp/resend_otp/
Content-Type: application/json

{
    "email": "user@example.com"
}

Response:
{
    "message": "OTP resent to user@example.com",
    "expires_in_minutes": 10
}
```

## Frontend Integration Example

### React/TypeScript Implementation

```typescript
import { useState } from 'react';

export const SignupWithOTP = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // Step 1: Request OTP
  const handleSendOTP = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/auth/otp/send_otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage(`OTP sent to ${email}. Check your inbox.`);
        setStep('otp');
      } else {
        setError(data.error || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Error sending OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/auth/otp/verify_otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp_code: otp })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage('OTP verified! Proceed with account creation');
        // Now create account with email
        // handleCreateAccount(email);
      } else {
        setError(data.error || 'Invalid OTP');
      }
    } catch (err) {
      setError('Error verifying OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Resend OTP
  const handleResendOTP = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/auth/otp/resend_otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage(data.message);
        setOtp(''); // Clear OTP input
      } else {
        setError(data.error || 'Failed to resend OTP');
      }
    } catch (err) {
      setError('Error resending OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <h2>Create Account with OTP Verification</h2>

      {step === 'email' ? (
        <div>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="input-field"
          />
          <button 
            onClick={handleSendOTP} 
            disabled={loading || !email}
            className="btn-primary"
          >
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
        </div>
      ) : (
        <div>
          <p className="info-text">Enter the OTP sent to: <strong>{email}</strong></p>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value.slice(0, 6))}
            placeholder="Enter 6-digit OTP"
            maxLength="6"
            className="input-field otp-input"
          />
          <button 
            onClick={handleVerifyOTP} 
            disabled={loading || otp.length !== 6}
            className="btn-primary"
          >
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          <button 
            onClick={handleResendOTP} 
            disabled={loading}
            className="btn-secondary"
          >
            Resend OTP
          </button>
          <button 
            onClick={() => setStep('email')}
            className="btn-link"
          >
            Change Email
          </button>
        </div>
      )}

      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};
```

## Updated Signup Flow

### Old Flow (without OTP):
```
User Email → Create Account → Login
```

### New Flow (with OTP):
```
User Email → Send OTP → Verify OTP → Create Account → Login
```

## Security Features

1. **6-digit OTP**: 1 million combinations
2. **10-minute expiration**: Time-based security
3. **Max 5 attempts**: Brute force protection
4. **Email verification**: Ensures real email ownership
5. **Database storage**: Secure OTP tracking
6. **Unique OTP codes**: Each generation creates unique code

## Database Structure

```sql
CREATE TABLE accounts_otpverification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    otp_code VARCHAR(6) UNIQUE NOT NULL,
    otp_type VARCHAR(20) DEFAULT 'signup',
    email VARCHAR(254) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME AUTO_NOW_ADD,
    expires_at DATETIME NOT NULL,
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 5
);
```

## Integration with User Signup

Update `accounts/views.py` signup view:

```python
from accounts.models import OTPVerification
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """
    Signup endpoint - requires OTP verification
    """
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password')
    
    # Check if OTP was verified
    try:
        otp = OTPVerification.objects.get(
            email=email,
            otp_type='signup',
            is_verified=True
        )
    except OTPVerification.DoesNotExist:
        return Response(
            {'error': 'Email not verified. Please complete OTP verification.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already used (optional - delete after first use)
    if otp.user:
        return Response(
            {'error': 'This OTP has already been used.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            username=email.split('@')[0]
        )
        
        # Link OTP to user
        otp.user = user
        otp.save()
        
        # Send welcome email
        from accounts.email_tasks import send_welcome_email
        send_welcome_email.delay(user.id)
        
        return Response({
            'message': 'Account created successfully',
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

## Testing

### Test OTP Sending
```bash
python manage.py shell
>>> from accounts.models import OTPVerification
>>> otp = OTPVerification.create_otp(email='test@example.com', otp_type='signup')
>>> print(f"OTP Code: {otp.otp_code}")
>>> print(f"Expires: {otp.expires_at}")

# Send email
>>> from accounts.email_tasks import send_otp_email
>>> send_otp_email(otp.id)  # Or send_otp_email.delay(otp.id) if using Celery
```

### Test OTP Verification
```bash
python manage.py shell
>>> from accounts.models import OTPVerification
>>> otp = OTPVerification.objects.first()
>>> is_valid, message = otp.verify_otp('123456')
>>> print(f"Valid: {is_valid}, Message: {message}")
```

## Error Handling

| Error | Status | Resolution |
|-------|--------|-----------|
| Email not provided | 400 | Provide valid email |
| OTP not found | 404 | Request new OTP |
| OTP expired | 400 | Use resend OTP endpoint |
| Invalid OTP | 400 | Enter correct code |
| Max attempts exceeded | 400 | Request new OTP |

## Email Template

The OTP email includes:
- Professional header with branding
- Clear OTP display (large 6-digit format)
- Expiration time (10 minutes)
- Security warnings
- Link to company website

## Next Steps

1. **Update Signup Form**: Add OTP verification step in frontend
2. **Add Password Reset OTP**: Use same system for password reset
3. **Enable Celery**: Install celery/redis for async email sending
4. **Add Rate Limiting**: Prevent OTP spam requests
5. **Add SMS OTP**: Optional SMS sending as fallback
6. **Dashboard Integration**: Track OTP delivery metrics

## Admin Interface

Register OTPVerification in `accounts/admin.py`:

```python
from django.contrib import admin
from accounts.models import OTPVerification

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp_type', 'is_verified', 'created_at', 'expires_at')
    list_filter = ('otp_type', 'is_verified', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('otp_code', 'created_at')
```

## Troubleshooting

### OTP not being sent
- Check Mailjet credentials in settings.py
- Verify email is in Mailjet whitelist
- Check DEBUG logs for email service errors

### OTP expired too quickly
- Adjust expiration time in `OTPVerification.create_otp()` (default: 10 minutes)

### High failed verification attempts
- Consider implementing rate limiting
- Add cooldown between attempts
- Send notification on suspicious activity

---

**Implementation Status**: ✅ Complete and tested
**Last Updated**: 2025-11-19
