# Wallet Top-Up Quick Reference

## API Endpoints

### Create Top-Up Request
```
POST /api/promotions/wallet-topups/initiate_payment/
{
    "amount": 100.00,
    "payment_method": "credit_card"  # or "bank_transfer"
}

Response:
{
    "id": 1,
    "user_id": 123,
    "amount": "100.00",
    "status": "processing",
    "payment_method": "credit_card",
    "created_at": "2025-11-26T10:00:00Z"
}
```

### Get Current Balance
```
GET /api/promotions/wallet-topups/current_balance/

Response:
{
    "balance": 500.00,
    "total_earnings": 1250.00,
    "available": 1750.00
}
```

### List User's Top-Ups
```
GET /api/promotions/wallet-topups/

Response:
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 5,
            "user_id": 123,
            "amount": "100.00",
            "status": "completed",
            ...
        }
    ]
}
```

### Admin: Complete Top-Up
```
POST /api/promotions/wallet-topups/{id}/complete/

Response:
{
    "detail": "Top-up of $100.00 completed successfully",
    "topup": {...},
    "new_balance": 600.00
}
```

### Admin: Mark as Failed
```
POST /api/promotions/wallet-topups/{id}/fail/
{
    "error_message": "Payment declined"
}
```

## Frontend Usage

### Import Component
```typescript
import WalletTopUpModal from '../components/promotions/WalletTopUpModal';
```

### Use in Component
```typescript
const [showTopUpModal, setShowTopUpModal] = useState(false);

// In render:
<WalletTopUpModal
  isOpen={showTopUpModal}
  onClose={() => setShowTopUpModal(false)}
  onSuccess={() => refetchBalance()}
  currentBalance={balance}
/>

// To open modal:
<button onClick={() => setShowTopUpModal(true)}>Top Up</button>
```

## Admin Panel

### Access
Dashboard → Promotions → Wallet Top-ups

### Features
- View all top-ups with status
- Filter by status, payment method, date
- Search by user, email, transaction ID
- Bulk actions: Mark as Completed, Mark as Failed
- See timestamps for audit trail

### Workflow
1. User initiates top-up via API
2. Admin reviews in panel
3. Admin verifies payment confirmation
4. Admin clicks "Mark as Completed"
5. System automatically adds funds to user wallet

## Validation Rules

| Field | Min | Max | Rules |
|-------|-----|-----|-------|
| Amount | $1.00 | $10,000 | Positive decimal, max 2 decimals |
| Payment Method | - | - | "credit_card" or "bank_transfer" |

## Status Lifecycle

```
User Initiates
    ↓
pending (default for new requests)
    ↓
processing (user submits payment)
    ↓
completed (admin approves) → Wallet updated ✓
    ↓
[OR]
failed (payment declined) → No funds added

[OR] 
cancelled (user/admin cancels) → No funds added
```

## Error Messages

| Scenario | Message |
|----------|---------|
| Amount ≤ 0 | "Top-up amount must be positive" |
| Amount < $1 | "Minimum top-up amount is $1.00" |
| Amount > $10,000 | "Maximum top-up amount is $10,000" |
| Invalid format | "Invalid amount format" |
| No amount | "Amount is required" |

## Database Fields

### WalletTopUp Table
- `id` - Primary key
- `user_id` - FK to User
- `amount` - Decimal(10,2)
- `status` - CharField with choices
- `payment_method` - CharField
- `transaction_id` - CharField, unique
- `payment_reference` - CharField
- `notes` - TextField
- `created_at` - DateTimeField (auto)
- `updated_at` - DateTimeField (auto)
- `completed_at` - DateTimeField (nullable)

### Related: UserProfile.balance
- Type: Decimal(12,2)
- Updated when top-up is completed
- Also tracks total_earnings separately

## Common Tasks

### Check User's Balance
```python
from accounts.models import UserProfile

profile = UserProfile.objects.get(user_id=123)
print(f"Balance: ${profile.balance}")
print(f"Total Earnings: ${profile.total_earnings}")
print(f"Available: ${profile.balance + profile.total_earnings}")
```

### Process Pending Top-Ups
```python
from promotions.models import WalletTopUp

# Get all pending
pending = WalletTopUp.objects.filter(status='pending')

# Complete one
topup = pending.first()
topup.mark_completed()  # Updates wallet balance automatically
```

### View Top-Up History
```python
from promotions.models import WalletTopUp

user_topups = WalletTopUp.objects.filter(user_id=123)
completed = user_topups.filter(status='completed')
total_added = completed.aggregate(total=Sum('amount'))['total']
```

## Integration Checklist

- [x] Model created and migrated
- [x] Admin panel configured
- [x] API endpoints built
- [x] Serializers with validation
- [x] ViewSet with permissions
- [x] Frontend modal component
- [x] PromotionsPage integration
- [x] System checks passing
- [x] Ready for deployment

## Support

For issues or questions:
1. Check Django logs: `python manage.py runserver`
2. Check browser console for frontend errors
3. Verify API endpoints in Django admin
4. Check user permissions and authentication
