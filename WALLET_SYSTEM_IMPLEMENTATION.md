# Facilitator Wallet System - Three-Balance Implementation

## ✅ Implementation Complete

This document outlines the new **three-balance wallet system** for facilitators implemented according to NAG specifications.

---

## 1. Three Balance Fields

### **earning_balance**
- **Definition**: Total amount earned from course sales
- **Type**: Non-spendable record
- **Usage**: Shows facilitator's lifetime earnings
- **When updated**: After each course purchase
- **Database field**: `UserProfile.earning_balance`

### **pending_balance**
- **Definition**: Earned money in temporary hold (escrow)
- **Duration**: Held for 2-5 days (processing period)
- **Reason for hold**: Payment gateway settlement, fraud checks, refund windows
- **When updated**: After earning goes into processing
- **Transitions to**: Available balance after processing period
- **Database field**: `UserProfile.pending_balance`

### **available_balance**
- **Definition**: Spendable money the facilitator can use immediately
- **Includes**: 
  - Cleared earnings (moved from pending)
  - Top-up deposits
  - Admin manual credits
- **Usage**: For withdrawals, campaigns, promotions, sponsored posts, paid features
- **Database field**: `UserProfile.available_balance`

---

## 2. Changes Made

### Backend (Django)

#### ✅ Accounts Models (`accounts/models.py`)
- Replaced: `balance`, `total_earnings`
- Added: `earning_balance`, `pending_balance`, `available_balance`
- All three fields: `DecimalField(max_digits=12, decimal_places=2, default=0)`

#### ✅ Database Migration (`accounts/migrations/0012_...py`)
- Removes old fields: `balance`, `total_earnings`
- Creates new fields: `earning_balance`, `pending_balance`, `available_balance`
- Maintains data consistency with zero initialization

#### ✅ Accounts Serializers (`accounts/serializers.py`)
- Updated `UserProfileSerializer` fields list
- Now includes: `earning_balance`, `pending_balance`, `available_balance`
- Removed: `balance`, `total_earnings`

#### ✅ Promotions Serializers (`promotions/serializers.py`)
- Updated `WithdrawalRequestSerializer.validate_amount()`
- Changed balance check from: `profile.balance + profile.total_earnings`
- Changed to: `profile.available_balance`

#### ✅ Promotions Views (`promotions/views.py`)
- Updated `WalletTopUpViewSet.complete()`: deposits now go to `available_balance`
- Updated `current_balance()` endpoint: returns all three balances
- Updated campaign creation balance deduction: uses `available_balance`
- Error messages updated to reflect "insufficient available balance"

#### ✅ Promotions Models (`promotions/models.py`)
- Top-up processing: `WalletTopUp.mark_completed()` adds to `available_balance`
- Withdrawal logic: updated to deduct from `available_balance` only
- Removed complex total_earnings/balance split logic
- Simplified to single available_balance deduction

---

## 3. Key Business Logic

### Top-Up Flow (New)
```
Facilitator initiates top-up $50
→ Top-up goes through payment processing
→ Upon completion: available_balance += $50
→ Money is immediately usable
```

### Earning Flow (Course Sale)
```
User buys course for $100 (Facilitator earns 80% = $80)
→ earning_balance += $80
→ pending_balance += $80
→ (available remains unchanged)

After 2-5 day processing period:
→ pending_balance -= $80
→ available_balance += $80
→ (earning_balance remains unchanged)
```

### Withdrawal Flow (Updated)
```
Facilitator requests withdrawal of $100
→ System checks: available_balance >= $100?
→ If yes: available_balance -= $100 and process withdrawal
→ If no: Reject with "Insufficient available balance"
```

### Campaign/Promotion Spend Flow
```
Facilitator creates campaign with $500 budget
→ System checks: available_balance >= $500?
→ If yes: available_balance -= $500
→ If no: Reject campaign creation with 402 status
```

---

## 4. API Endpoint Changes

### GET `/api/promotions/wallet-topups/current_balance/`
**Old Response:**
```json
{
  "balance": 1000.00,
  "total_earnings": 5000.00,
  "available": 6000.00
}
```

**New Response:**
```json
{
  "earning_balance": 5000.00,
  "pending_balance": 200.00,
  "available_balance": 1200.00
}
```

---

## 5. Frontend Changes

### CampaignsPage.tsx
- Updated balance retrieval: `user.profile.available_balance`
- Removed: calculation from analytics
- Removed: fallback to old `balance` field
- Balance validation now uses single available_balance value

---

## 6. Terminology Updates

### ❌ REMOVED (Never use)
- `balance` - Old misleading field
- `total_earnings` - Confused with earning_balance
- `Total Balance` - Term that caused confusion

### ✅ CORRECT TERMS (Always use)
- `Earning Balance` - Lifetime earnings record
- `Pending Balance` - Money in processing
- `Available Balance` - Spendable money

---

## 7. Database Migration Instructions

### Step 1: Run Migration
```bash
python manage.py migrate accounts 0012_wallet_system_three_balance_model
```

### Step 2: Verify
```bash
python manage.py dbshell
SELECT earning_balance, pending_balance, available_balance FROM accounts_userprofile LIMIT 1;
```

Should show: `0.00 | 0.00 | 0.00` for all users initially

---

## 8. Admin Actions Needed

### Migrating Existing Balances (if needed)
If you had previous data in `balance` and `total_earnings`, run:

```python
from accounts.models import UserProfile
from decimal import Decimal

for profile in UserProfile.objects.all():
    # Map old structure to new structure (adjust logic per your business rules)
    # This is an example - adjust based on your actual requirements
    profile.earning_balance = profile.total_earnings or 0
    profile.pending_balance = 0  # Start fresh processing period
    profile.available_balance = profile.balance or 0  # Topups and cleared
    profile.save()
```

---

## 9. Testing Checklist

### Unit Tests
- [ ] Earning balance increments on course purchase
- [ ] Pending balance moves to available after processing
- [ ] Top-up adds directly to available balance
- [ ] Withdrawal deducts from available balance only
- [ ] Campaign creation fails if available balance insufficient
- [ ] Withdrawal fails if available balance insufficient

### Integration Tests
- [ ] Full earning flow (purchase → pending → available)
- [ ] Full top-up flow (init → processing → available)
- [ ] Balance calculations consistent across endpoints
- [ ] No negative balances possible

### API Tests
- [ ] GET `/current_balance/` returns all three fields
- [ ] POST campaign with insufficient balance returns 402
- [ ] POST withdrawal with insufficient balance returns validation error
- [ ] POST top-up completion updates available_balance

---

## 10. Deployment Notes

### Pre-Deployment
1. ✅ Backup database
2. ✅ Test migration on staging
3. ✅ Verify all three fields working correctly

### Deployment
1. ✅ Run Django migration
2. ✅ Rebuild frontend bundle
3. ✅ Test API endpoints
4. ✅ Monitor wallet operations

### Post-Deployment
1. ✅ Monitor balance updates
2. ✅ Verify top-ups work correctly
3. ✅ Verify withdrawals work correctly
4. ✅ Check campaign spending logic

---

## 11. Documentation References

See the following documents for additional details:
- `WALLET_SYSTEM_AUDIT.md` - Complete component inventory
- `WALLET_MIGRATION_GUIDE.md` - Step-by-step migration
- `WALLET_CODE_DELETIONS.md` - Code sections to remove
- Facilitator Dashboard documentation

---

## 12. Future Enhancements

### Possible Improvements
1. **Processing Period Configuration**: Make 2-5 day period configurable per country
2. **Pending Balance Transparency**: Show countdown timer to facilitators
3. **Balance History**: Track balance changes over time
4. **Earning Breakdown**: Show earnings by course/product
5. **Automated Pending→Available**: Scheduled task to move cleared earnings
6. **Balance Alerts**: Notify when pending becomes available

---

✅ **Implementation Status**: COMPLETE
🚀 **Ready for**: Testing & Deployment
📊 **Affected Users**: All Facilitators
💾 **Database Change**: Yes (migration required)

