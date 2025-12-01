# Wallet System - Complete Search Index

**Generated:** November 27, 2025  
**Scope:** All wallet, balance, earnings, and withdrawal references in codebase

---

## 1. BACKEND MODELS & CLASSES

### File: `promotions/models.py`

| Component | Type | Lines | Status |
|-----------|------|-------|--------|
| FacilitatorEarning | Model | 253-263 | REMOVE |
| WithdrawalRequest | Model | 268-360 | REMOVE |
| WalletTopUp | Model | 362-430 | REMOVE |
| FacilitatorEarning.earned_at | Field | 256 | REMOVE |
| FacilitatorEarning.is_paid | Field | 257 | REMOVE |
| WithdrawalRequest.process() | Method | ~280-360 | REMOVE |
| WalletTopUp.mark_completed() | Method | ~380-410 | REMOVE |
| WalletTopUp.mark_failed() | Method | ~412-418 | REMOVE |

### File: `accounts/models.py`

| Component | Type | Lines | Status |
|-----------|------|-------|--------|
| UserProfile.balance | Field | 58 | REMOVE |
| UserProfile.total_earnings | Field | 60 | REMOVE |

---

## 2. BACKEND SERIALIZERS

### File: `promotions/serializers.py`

| Component | Type | Lines | Status |
|-----------|------|-------|--------|
| WithdrawalRequestSerializer | Serializer | 14-53 | REMOVE |
| WithdrawalRequestSerializer.get_total_earnings() | Method | 27-30 | REMOVE |
| WithdrawalRequestSerializer.get_pending_amount() | Method | 32-36 | REMOVE |
| WithdrawalRequestSerializer.validate_amount() | Method | 39-53 | REMOVE |
| WalletTopUpSerializer | Serializer | 215-244 | REMOVE |
| WalletTopUpSerializer.validate_amount() | Method | 226-232 | REMOVE |
| WalletTopUpSerializer.create() | Method | 234-238 | REMOVE |

### File: `accounts/serializers.py`

| Component | Type | Status |
|-----------|------|--------|
| balance field | Any serializer referencing it | REMOVE |
| total_earnings field | Any serializer referencing it | REMOVE |

---

## 3. BACKEND API VIEWS & VIEWSETS

### File: `promotions/views.py`

| Component | Type | Details | Status |
|-----------|------|---------|--------|
| WalletTopUpViewSet | ViewSet | Entire class with 8 custom actions | REMOVE |
| WithdrawalRequestViewSet | ViewSet | Entire class with 4 custom actions | REMOVE |
| SponsorCampaignViewSet.start_campaign() | Method | Lines ~122-127 (balance deduction) | MODIFY |

**WalletTopUpViewSet Actions:**
- `list()` - GET /wallet-topups/
- `create()` - POST /wallet-topups/
- `retrieve()` - GET /wallet-topups/{id}/
- `update()` - PATCH /wallet-topups/{id}/
- `initiate_payment()` - POST /wallet-topups/initiate_payment/
- `complete()` - POST /wallet-topups/{id}/complete/
- `fail()` - POST /wallet-topups/{id}/fail/
- `current_balance()` - GET /wallet-topups/current_balance/

**WithdrawalRequestViewSet Actions:**
- `list()` - GET /withdrawals/
- `create()` - POST /withdrawals/
- `retrieve()` - GET /withdrawals/{id}/
- `update()` - PATCH /withdrawals/{id}/
- `approve()` - POST /withdrawals/{id}/approve/
- `reject()` - POST /withdrawals/{id}/reject/
- `complete()` - POST /withdrawals/{id}/complete/

### File: `promotions/dashboard_analytics.py`

| Component | Type | Lines | Status |
|-----------|------|-------|--------|
| FacilitatorAnalyticsView.get() | Method | 218-222 (available_balance calc) | REMOVE |
| available_balance calculation | Logic | 6 lines | REMOVE |
| DashboardAnalyticsView | View | (minor changes) | MODIFY |

---

## 4. BACKEND URL ROUTING

### File: `promotions/urls.py`

| Route | ViewSet | Status |
|-------|---------|--------|
| wallet-topups | WalletTopUpViewSet | REMOVE |
| withdrawals | WithdrawalRequestViewSet | REMOVE |

---

## 5. FRONTEND HOOKS

### File: `frontend/src/hooks/dashboardAnalytics.ts`

| Component | Type | Details |
|-----------|------|---------|
| useFacilitatorAnalytics() | Hook | Returns FacilitatorAnalyticsSummary (contains available_balance) |

### File: `frontend/src/hooks/usePromotions.ts`

| Component | Type | Status |
|-----------|------|--------|
| availableBalance | State | REMOVE (line ~32) |
| Balance calculation logic | Logic | REMOVE (lines ~35-40) |
| availableBalance in return | Return value | REMOVE |

### File: `frontend/src/hooks/useWithdrawals.ts`

| Component | Type | Status |
|-----------|------|--------|
| useWithdrawals() | Hook | DELETE ENTIRE FILE |
| Withdrawal interface | Interface | DELETE ENTIRE FILE |
| WithdrawalRequest interface | Interface | DELETE ENTIRE FILE |

---

## 6. FRONTEND PAGES & COMPONENTS

### File: `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx`

| Line | Component | Type | Status |
|------|-----------|------|--------|
| 10 | useFacilitatorAnalytics import | Import | REMOVE (if only used for wallet) |
| 47 | useFacilitatorAnalytics hook call | Hook Call | REMOVE |
| 87-90 | walletBalance calculation | Logic | REMOVE |
| 138 | createCampaignWithStatus function | Method | MODIFY (remove balance check) |
| 144-145 | Balance validation error toast | UI | REMOVE |
| 308-309 | Wallet Balance display section | UI | REMOVE |
| 627 | Remaining balance calculation | UI | REMOVE |
| 744 | Minimum balance info text | UI | REMOVE |
| 767 | Button disabled state (balance check) | UI | MODIFY |

---

## 7. ANALYTICS ENDPOINTS

### Current API Responses Including Wallet Data

**Endpoint:** `GET /api/promotions/analytics/facilitator/?days=30`

**Current Response Structure:**
```json
{
  "total_earnings": 1250.00,
  "total_students": 42,
  "avg_rating": 4.5,
  "total_courses": 3,
  "earning_trends": [...],
  "enrollment_trends": [...],
  "course_performance": [...],
  "rating_distribution": [...],
  "engagement_by_type": [...],
  "available_balance": 1750.00,  // ← REMOVE THIS
  "period_days": 30,
  "growth_stats": {...}
}
```

**References in Code:**
- `CampaignsPage.tsx` (line 47, 88)
- `usePromotions.ts` (analytics loading)
- `useFacilitatorAnalytics.ts` (hook)

---

## 8. DATABASE QUERIES & ORM CALLS

### Balance Deduction Logic

**Location:** `promotions/views.py::SponsorCampaignViewSet.start_campaign()`

```python
# Lines ~122-127
if status != 'draft' and budget > 0:
    updated = UserProfile.objects.filter(user=user, balance__gte=budget).update(balance=F('balance') - budget)
    if updated == 0:
        return Response({'error': 'Insufficient balance'}, status=402)
```

### Withdrawal Balance Deduction

**Location:** `promotions/models.py::WithdrawalRequest.process()`

```python
# Lines ~327-340
if total_earnings >= withdrawal_amount:
    new_total_earnings = total_earnings - withdrawal_amount
    new_balance = balance
else:
    amount_to_deduct_from_balance = withdrawal_amount - total_earnings
    new_total_earnings = Decimal('0')
    new_balance = max(balance - amount_to_deduct_from_balance, Decimal('0'))

profile.total_earnings = new_total_earnings
profile.balance = new_balance
profile.save()
```

### Top-Up Balance Addition

**Location:** `promotions/models.py::WalletTopUp.mark_completed()`

```python
# Lines ~380-410
profile.balance = (profile.balance or Decimal('0')) + Decimal(str(self.amount))
profile.save()
```

---

## 9. ADMIN INTERFACE REFERENCES

### Models Registered in Admin (likely)

- `WalletTopUp` (in `promotions/admin.py`)
- `WithdrawalRequest` (in `promotions/admin.py`)
- `FacilitatorEarning` (in `promotions/admin.py`)

**Note:** These need to be unregistered from Django admin after model deletion.

---

## 10. DOCUMENTATION FILES

### Files Containing Wallet References

| File | Type | Status |
|------|------|--------|
| WALLET_TOPUP_QUICK_REFERENCE.md | Documentation | DELETE |
| Any README mentioning wallet | Documentation | UPDATE/REMOVE |

---

## 11. TEST FILES & FIXTURES

### Potential Test Files (Search Results)

```bash
# Run to find test references:
grep -r "wallet\|topup\|withdrawal\|balance" . \
  --include="*test*.py" \
  --include="*test*.tsx"
```

---

## 12. CONFIGURATION & SETTINGS

### Django Settings to Check

- `INSTALLED_APPS` - Verify no separate wallet app
- `REST_FRAMEWORK` settings - Check permissions/serializers
- Any custom middleware related to balance

---

## 13. IMPORT STATEMENTS TO REMOVE

### Backend Python Imports

```python
# In promotions/views.py:
from .models import SponsorCampaign, EngagementLog, WithdrawalRequest, WalletTopUp  # Remove WithdrawalRequest, WalletTopUp
from .serializers import WithdrawalRequestSerializer, WalletTopUpSerializer  # REMOVE ENTIRE IMPORT

# In promotions/serializers.py:
from .models import WithdrawalRequest, FacilitatorEarning, WalletTopUp  # REMOVE

# In promotions/dashboard_analytics.py:
from .models import FacilitatorEarning  # Remove if unused elsewhere
```

### Frontend TypeScript Imports

```typescript
// In CampaignsPage.tsx:
import { useFacilitatorAnalytics } from '../../../hooks/dashboardAnalytics';  // Remove if only for wallet

// Anywhere using useWithdrawals:
import { useWithdrawals } from '../../../hooks/useWithdrawals';  // REMOVE ALL
```

---

## 14. TYPE DEFINITIONS

### TypeScript Types to Update

**File:** `frontend/src/types/analytics.ts` (or similar)

```typescript
interface FacilitatorAnalyticsSummary {
  total_earnings: number;
  total_students: number;
  available_balance?: number;  // ← REMOVE THIS FIELD
  course_performance: Array<any>;
  // ... other fields
}
```

---

## 15. PAYMENT/TRANSACTION REFERENCES

### Related Models (Keep - Not to Remove)

| Model | File | Status |
|-------|------|--------|
| SponsorCampaign | promotions/models.py | KEEP |
| EngagementLog | promotions/models.py | KEEP |
| CampaignAnalytics | promotions/models.py | KEEP |
| PromotionMetrics | promotions/models.py | KEEP |

---

## 16. SEARCH PATTERNS

### Grep Patterns Used for Audit

```bash
# Pattern 1: Wallet references
grep -r "wallet\|topup\|Wallet" . --include="*.py" --include="*.tsx" --include="*.ts"

# Pattern 2: Balance references
grep -r "balance\|earnings\|available" . --include="*.py" --include="*.tsx" --include="*.ts"

# Pattern 3: Withdrawal references
grep -r "withdrawal\|Withdrawal" . --include="*.py" --include="*.tsx" --include="*.ts"

# Pattern 4: Total Balance references
grep -r "total.*balance\|Total.*Balance" . --include="*.py" --include="*.tsx" --include="*.ts"

# Pattern 5: Facilitator references (related to earnings)
grep -r "facilitator.*earning\|earnings.*facilitator" . --include="*.py"
```

---

## 17. API RESPONSE SAMPLES

### Current Endpoints Returning Wallet Data

**Endpoint 1:** `GET /api/promotions/wallet-topups/`
```json
[
  {
    "id": 1,
    "user_id": 5,
    "amount": "100.00",
    "status": "completed",
    "payment_method": "credit_card",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "completed_at": "2025-01-15T10:35:00Z"
  }
]
```

**Endpoint 2:** `GET /api/promotions/wallet-topups/current_balance/`
```json
{
  "balance": 500.00,
  "total_earnings": 1250.00,
  "available": 1750.00
}
```

**Endpoint 3:** `GET /api/promotions/withdrawals/`
```json
[
  {
    "id": 1,
    "amount": "100.00",
    "status": "pending",
    "bank_name": "Bank of Example",
    "account_number": "****1234",
    "account_name": "John Doe",
    "requested_at": "2025-01-15T09:00:00Z",
    "processed_at": null,
    "total_earnings": 1250.00,
    "pending_amount": 500.00
  }
]
```

---

## SUMMARY TABLE

### All Components by Category

| Category | Count | Action |
|----------|-------|--------|
| Models | 3 | Remove |
| ViewSets | 2 | Remove |
| Serializers | 2 | Remove |
| Views/Methods | 8+ | Remove/Modify |
| Frontend Hooks | 3 | Remove/Modify |
| UI Components | 1 page | Modify (8 locations) |
| URL Routes | 2 | Remove |
| API Endpoints | 15+ | Remove |
| Database Fields | 2 | Remove |
| Database Models | 3 | Remove |
| Documentation Files | 1 | Delete |
| Config Changes | ~3 | Apply |

**Total Components:** 45+  
**Total Removal Operations:** 30+  
**Total Modification Operations:** 15+

---

**End of Search Index**

All wallet system components have been cataloged and are ready for removal.

