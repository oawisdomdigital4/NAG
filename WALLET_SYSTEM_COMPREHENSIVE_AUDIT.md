# Facilitator Wallet System - Comprehensive Audit Report

**Date:** November 27, 2025  
**Scope:** Complete wallet/balance/earnings system across Django backend and React frontend

---

## Executive Summary

The facilitator wallet system currently consists of:
- **2 main database models** (WalletTopUp, WithdrawalRequest) + support models (FacilitatorEarning)
- **2 UserProfile fields** (balance, total_earnings) storing wallet state
- **3 API viewsets** with 8+ custom endpoints for wallet operations
- **Backend analytics endpoints** returning available_balance
- **Frontend components** consuming wallet balance data from campaigns page

---

## 1. BACKEND WALLET SYSTEM

### 1.1 Database Models (Django)

#### Location: `promotions/models.py`

**Model 1: WalletTopUp**
```python
class WalletTopUp(models.Model):
    # Track wallet top-up transactions for promotions budget
    user = ForeignKey(User)
    amount = DecimalField
    status = CharField(choices=['pending', 'processing', 'completed', 'failed', 'cancelled'])
    payment_method = CharField  # 'credit_card', 'bank_transfer', 'paypal'
    transaction_id = CharField(unique=True)
    payment_reference = CharField
    notes = TextField
    created_at, updated_at, completed_at = DateTimeFields
```

**Key Methods:**
- `mark_completed()` - Adds amount to user.profile.balance
- `mark_failed(error_message)` - Sets status to 'failed'

**Model 2: WithdrawalRequest**
```python
class WithdrawalRequest(models.Model):
    # Track withdrawal requests from facilitators
    facilitator = ForeignKey(User)
    amount = DecimalField
    status = CharField(choices=['pending', 'approved', 'rejected', 'completed'])
    bank_name, account_number, account_name = CharField
    notes = TextField
    requested_at, processed_at = DateTimeFields
    processed_by = ForeignKey(User)
```

**Key Methods:**
- `process(status, processed_by, notes)` - Processes withdrawal and **DEDUCTS from user balance**:
  - First deducts from `total_earnings`
  - Then deducts from `balance`
  - Sets `FacilitatorEarning.is_paid = True`

**Model 3: FacilitatorEarning**
```python
class FacilitatorEarning(models.Model):
    facilitator = ForeignKey(User)
    amount = DecimalField
    source = CharField  # 'course_sale', 'sponsorship', etc.
    description = TextField
    earned_at = DateTimeField
    is_paid = BooleanField(default=False)
```

#### Location: `accounts/models.py`

**UserProfile Wallet Fields:**
```python
class UserProfile(models.Model):
    balance = DecimalField(max_digits=12, default=0)           # Available balance for payouts
    total_earnings = DecimalField(max_digits=12, default=0)    # Total earnings (earned but not withdrawn)
```

**Important Note:** `available_balance = balance + total_earnings` (calculated, not stored)

---

### 1.2 API Endpoints

#### Location: `promotions/views.py`

**ViewSet 1: WalletTopUpViewSet**
- **Base URL:** `/api/promotions/wallet-topups/`
- **CRUD Operations:**
  - `GET /` - List user's top-ups
  - `POST /` - Create new top-up request
  - `GET /{id}/` - Retrieve top-up details
  - `PATCH /{id}/` - Update top-up

- **Custom Actions:**
  - `POST /initiate_payment/` - Initiate payment (creates WalletTopUp with status='processing')
    - Input: `{amount, payment_method}`
    - Output: WalletTopUp record
  
  - `POST /{id}/complete/` (Admin only) - Mark top-up as completed
    - Action: Calls `topup.mark_completed()` → adds amount to user.profile.balance
    - Output: Returns new_balance
  
  - `POST /{id}/fail/` (Admin only) - Mark top-up as failed
    - Input: `{error_message}`
  
  - `GET /current_balance/` - Get current wallet state
    - Output: `{balance, total_earnings, available}`

**ViewSet 2: WithdrawalRequestViewSet**
- **Base URL:** `/api/promotions/withdrawals/`
- **CRUD Operations:**
  - `GET /` - List user's withdrawals (or all if admin)
  - `POST /` - Create withdrawal request
  - `GET /{id}/` - Retrieve withdrawal details

- **Custom Actions:**
  - `POST /{id}/approve/` (Admin only) - Approve withdrawal
    - Action: `withdrawal.process('approved', user, notes)`
    - Side Effect: **DEDUCTS amount from user balance**
  
  - `POST /{id}/reject/` (Admin only) - Reject withdrawal
    - Action: `withdrawal.process('rejected', user, notes)`
  
  - `POST /{id}/complete/` (Admin only) - Complete withdrawal
    - Action: `withdrawal.process('completed', user, notes)`
    - Side Effect: **DEDUCTS amount from user balance**

**Validation in WithdrawalRequestSerializer:**
```python
def validate_amount(self, value):
    # Minimum: $50
    # Maximum: balance + total_earnings (available balance)
    available_balance = float(profile.balance or 0) + float(profile.total_earnings or 0)
    if value > available_balance:
        raise ValidationError(f"Insufficient available balance. Available: ${available_balance:.2f}")
```

---

### 1.3 Analytics Endpoints

#### Location: `promotions/dashboard_analytics.py`

**Endpoint 1: DashboardAnalyticsView**
- **URL:** `GET /api/promotions/analytics/dashboard/?days=30`
- **Permission:** IsAuthenticated
- **Returns:** Comprehensive dashboard data including campaigns, earnings, engagement

**Endpoint 2: FacilitatorAnalyticsView** ⭐ **RETURNS available_balance**
- **URL:** `GET /api/promotions/analytics/facilitator/?days=30`
- **Permission:** IsAuthenticated
- **Returns:**
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
    "available_balance": 1750.00,
    "period_days": 30,
    "growth_stats": {...}
  }
  ```

**Key Calculation (Line 218-222):**
```python
profile = getattr(user, 'profile', None)
balance = float(getattr(profile, 'balance', 0) or 0)
total_earnings = float(getattr(profile, 'total_earnings', 0) or 0)
payload['available_balance'] = balance + total_earnings
```

---

### 1.4 Serializers

#### Location: `promotions/serializers.py`

**WalletTopUpSerializer**
```python
class WalletTopUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTopUp
        fields = ['id', 'user_id', 'amount', 'status', 'payment_method',
                 'transaction_id', 'payment_reference', 'notes',
                 'created_at', 'updated_at', 'completed_at']
```

**WithdrawalRequestSerializer**
```python
class WithdrawalRequestSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'amount', 'status', 'requested_at', 'processed_at',
                 'total_earnings', 'pending_amount', 'bank_name', 'account_number',
                 'account_name', 'notes']
```

---

### 1.5 URL Routes

#### Location: `promotions/urls.py`

```python
router.register(r'wallet-topups', WalletTopUpViewSet, basename='wallet-topup')
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawal')

urlpatterns = [
    path('analytics/dashboard/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('analytics/facilitator/', FacilitatorAnalyticsView.as_view(), name='facilitator-analytics'),
]
```

---

## 2. FRONTEND WALLET SYSTEM

### 2.1 React Hooks

#### Location: `frontend/src/hooks/`

**Hook 1: useFacilitatorAnalytics** (dashboardAnalytics.ts)
```typescript
export function useFacilitatorAnalytics(days = 30) {
  const [data, setData] = useState<FacilitatorAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet(`/api/promotions/analytics/facilitator/?days=${days}`)
      .then((response) => {
        setData(response);  // Contains available_balance
      })
      .catch(...)
  }, [days]);

  return { data, loading, error };
}
```

**Hook 2: usePromotions** (usePromotions.ts)
```typescript
export function usePromotions() {
  const [availableBalance, setAvailableBalance] = useState<number>(0);

  // Fetches FacilitatorAnalytics including available_balance
  const analyticsRes = await api.apiGet('/api/promotions/analytics/facilitator/?days=30');
  const balance = (analyticsRes && analyticsRes.available_balance) ? 
    Number(analyticsRes.available_balance) : 0;
  setAvailableBalance(balance);

  return { availableBalance };
}
```

**Hook 3: useWithdrawals** (useWithdrawals.ts)
```typescript
export function useWithdrawals() {
  const [withdrawals, setWithdrawals] = useState<Withdrawal[]>([]);
  
  const createWithdrawal = async (request: WithdrawalRequest) => {
    await apiPost('/api/promotions/withdrawals/', request);
  };
  
  return { withdrawals, createWithdrawal };
}
```

---

### 2.2 Frontend Pages/Components

#### Location: `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx`

**Wallet Integration Points:**

1. **Line 10:** Import analytics hook
   ```tsx
   import { useFacilitatorAnalytics } from '../../../hooks/dashboardAnalytics';
   ```

2. **Line 47:** Fetch analytics data
   ```tsx
   const { data: analytics } = useFacilitatorAnalytics(30);
   ```

3. **Lines 87-90:** Calculate wallet balance
   ```tsx
   const walletBalance = Number((analytics && (analytics as any).available_balance != null)
     ? (analytics as any).available_balance
     : ((user?.profile && (user.profile as any).balance) ?? 50000));
   ```

4. **Line 138:** Check balance before campaign creation
   ```tsx
   if (requireBalance && walletBalance < formData.budget) {
     showToast(`Insufficient wallet balance. Required: $${formData.budget}, Available: $${walletBalance.toFixed(2)}`, 'error');
   }
   ```

5. **Lines 308-309:** Display wallet balance UI
   ```tsx
   <p className="text-sm font-semibold opacity-90">Wallet Balance</p>
   <p className="text-2xl font-bold">${walletBalance.toFixed(2)}</p>
   ```

6. **Line 627:** Show remaining balance after campaign
   ```tsx
   Remaining balance: <strong>${(walletBalance - formData.budget).toFixed(2)}</strong>
   ```

7. **Line 744:** Display minimum balance info
   ```tsx
   <p className="text-xs text-gray-600 mt-2">Minimum: $10.00 | Current balance: ${walletBalance.toFixed(2)}</p>
   ```

8. **Line 767:** Disable create button if insufficient balance
   ```tsx
   disabled={!formData.title || !formData.description || walletBalance < formData.budget || isCreatingCampaign}
   ```

---

### 2.3 Campaign Creation Logic

#### Location: `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx` (Lines 138-160)

```typescript
const createCampaignWithStatus = async (status: string, requireBalance = true) => {
  // ...validation...
  
  if (requireBalance && walletBalance < formData.budget) {
    showToast(`Insufficient wallet balance...`, 'error');
    return;
  }
  
  // Campaign creation calls backend:
  // POST /api/promotions/sponsor-campaigns/start_campaign/
  // Which deducts budget from user.profile.balance if status != 'draft'
};
```

---

## 3. CAMPAIGN SPENDING LOGIC

### 3.1 Campaign Budget Deduction

#### Location: `promotions/views.py` (SponsorCampaignViewSet.start_campaign)

```python
if status != 'draft' and budget > 0:
    # Atomically decrement user profile balance
    updated = UserProfile.objects.filter(
        user=user, 
        balance__gte=budget
    ).update(balance=F('balance') - budget)
    
    if updated == 0:
        return Response({'error': 'Insufficient balance'}, status=402)
```

**Key Points:**
- Balance deduction happens **at campaign activation**, not creation
- If campaign status = 'draft', no deduction
- If campaign status = 'active' or 'under_review', balance is deducted
- Using atomic F() expressions for consistency

---

## 4. REFERENCED MODELS & SERIALIZERS

### 4.1 Payment Models (Community App)

#### Location: `community/models.py`
```python
class SponsorCampaign(models.Model):
    sponsor = ForeignKey(User)
    budget = DecimalField
    cost_per_view = DecimalField
    status = CharField(choices=[...])  # draft, active, completed, etc.
    payment_status = CharField
    payment_id = CharField
```

### 4.2 Campaign Analytics Models

#### Location: `promotions/models.py`
```python
class CampaignAnalytics(models.Model):
    campaign = ForeignKey(SponsorCampaign)
    spend = DecimalField

class PromotionMetrics(models.Model):
    campaign = ForeignKey(SponsorCampaign)
    spend = DecimalField
    roi = FloatField
```

---

## 5. FILES TO MODIFY/REMOVE

### 5.1 Backend Files

| File | Changes Needed |
|------|---|
| `promotions/models.py` | Remove WalletTopUp, WithdrawalRequest, FacilitatorEarning; Remove balance deduction logic |
| `promotions/serializers.py` | Remove WalletTopUpSerializer, WithdrawalRequestSerializer; Remove available_balance from responses |
| `promotions/views.py` | Remove WalletTopUpViewSet, WithdrawalRequestViewSet; Update SponsorCampaignViewSet.start_campaign() to not deduct balance |
| `promotions/urls.py` | Remove wallet-topups and withdrawals routes |
| `promotions/dashboard_analytics.py` | Remove available_balance calculation (lines 218-222) |
| `accounts/models.py` | Remove balance and total_earnings fields from UserProfile |
| `accounts/serializers.py` | Remove balance, total_earnings from serialized fields |

### 5.2 Frontend Files

| File | Changes Needed |
|------|---|
| `frontend/src/hooks/dashboardAnalytics.ts` | Remove available_balance from return |
| `frontend/src/hooks/useFacilitatorAnalytics()` | Adapt to new API response |
| `frontend/src/hooks/usePromotions.ts` | Remove availableBalance state |
| `frontend/src/hooks/useWithdrawals.ts` | Delete entire file (no withdrawals) |
| `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx` | Remove wallet balance display, validation, and calculations |

---

## 6. API ENDPOINTS TO REMOVE

### 6.1 Wallet Management Endpoints
```
DELETE: POST /api/promotions/wallet-topups/
DELETE: POST /api/promotions/wallet-topups/initiate_payment/
DELETE: POST /api/promotions/wallet-topups/{id}/complete/
DELETE: POST /api/promotions/wallet-topups/{id}/fail/
DELETE: GET /api/promotions/wallet-topups/current_balance/
```

### 6.2 Withdrawal Endpoints
```
DELETE: GET /api/promotions/withdrawals/
DELETE: POST /api/promotions/withdrawals/
DELETE: POST /api/promotions/withdrawals/{id}/approve/
DELETE: POST /api/promotions/withdrawals/{id}/reject/
DELETE: POST /api/promotions/withdrawals/{id}/complete/
```

---

## 7. TOTAL BALANCE REFERENCES

Searched entire codebase for "Total Balance" phrase:

- **promotions/models.py** (Line 322): "First deduct from total_earnings, then from balance" - **COMMENT**
- **promotions/dashboard_analytics.py** (Line 218): "Expose available balance: sum of balance and total_earnings" - **COMMENT**

**Note:** No UI elements explicitly display "Total Balance" as a labeled field. However:
- CampaignsPage displays "Wallet Balance" (Line 308)
- Serializers include "total_earnings" field
- Analytics endpoints return "available_balance"

---

## 8. SUMMARY TABLE

### Backend Wallet Components

| Component | Type | Status | Action |
|-----------|------|--------|--------|
| WalletTopUp | Model | Active | REMOVE |
| WithdrawalRequest | Model | Active | REMOVE |
| FacilitatorEarning | Model | Active | REMOVE |
| UserProfile.balance | Field | Active | REMOVE |
| UserProfile.total_earnings | Field | Active | REMOVE |
| WalletTopUpViewSet | ViewSet | Active | REMOVE |
| WithdrawalRequestViewSet | ViewSet | Active | REMOVE |
| WalletTopUpSerializer | Serializer | Active | REMOVE |
| WithdrawalRequestSerializer | Serializer | Active | REMOVE |
| FacilitatorAnalyticsView (available_balance) | Endpoint | Active | REMOVE |
| DashboardAnalyticsView | Endpoint | Active | MODIFY |
| start_campaign (balance deduction) | Method | Active | MODIFY |

### Frontend Wallet Components

| Component | Type | Status | Action |
|-----------|------|--------|--------|
| useFacilitatorAnalytics | Hook | Active | MODIFY |
| usePromotions (availableBalance) | Hook | Active | MODIFY |
| useWithdrawals | Hook | Active | REMOVE |
| CampaignsPage (walletBalance) | Page | Active | REMOVE |
| CampaignsPage (wallet UI) | UI | Active | REMOVE |

---

## 9. COMPLETE ENDPOINT INVENTORY

### Active Wallet Endpoints (Needs Removal)

#### Top-Ups
```
GET    /api/promotions/wallet-topups/                                    - List user's top-ups
POST   /api/promotions/wallet-topups/                                    - Create top-up
GET    /api/promotions/wallet-topups/{id}/                               - Get top-up details
PATCH  /api/promotions/wallet-topups/{id}/                               - Update top-up
POST   /api/promotions/wallet-topups/initiate_payment/                   - Initiate payment
POST   /api/promotions/wallet-topups/{id}/complete/                      - Complete top-up (ADMIN)
POST   /api/promotions/wallet-topups/{id}/fail/                          - Mark failed (ADMIN)
GET    /api/promotions/wallet-topups/current_balance/                    - Get balance info
```

#### Withdrawals
```
GET    /api/promotions/withdrawals/                                      - List withdrawals
POST   /api/promotions/withdrawals/                                      - Create withdrawal
GET    /api/promotions/withdrawals/{id}/                                 - Get withdrawal details
PATCH  /api/promotions/withdrawals/{id}/                                 - Update withdrawal
POST   /api/promotions/withdrawals/{id}/approve/                         - Approve (ADMIN)
POST   /api/promotions/withdrawals/{id}/reject/                          - Reject (ADMIN)
POST   /api/promotions/withdrawals/{id}/complete/                        - Complete (ADMIN)
```

---

## 10. CRITICAL WORKFLOW IMPACTS

### Current Workflow
1. User tops up wallet → funds added to `UserProfile.balance`
2. User creates campaign → if active, balance is deducted by budget amount
3. User withdraws funds → balance is deducted by withdrawal amount
4. Analytics shows: `available_balance = balance + total_earnings`

### Post-Removal Workflow
1. User creates campaign (no balance check needed)
2. Campaign status: draft/active/completed (no financial implications)
3. No withdrawal system
4. Analytics shows: only course/engagement metrics, no financial data

---

## 11. DATA CLEANUP REQUIRED

### Database Cleanup
```sql
-- After removal, existing data:
- WalletTopUp records: DELETE or archive
- WithdrawalRequest records: DELETE or archive
- FacilitatorEarning records: DELETE or archive
- UserProfile.balance and .total_earnings: SET to 0 or archive
```

### Frontend Data
```javascript
// Remove from localStorage/sessionStorage:
- availableBalance
- walletData
- topupTransactions
```

---

## 12. DEPENDENCIES & INTERACTIONS

### What depends on wallet system:
- ✅ CampaignsPage (budget validation)
- ✅ FacilitatorAnalytics hook (available_balance)
- ✅ Dashboard navbar (if it displays balance)
- ✅ Admin dashboard (withdrawal management)

### What wallet system depends on:
- ✅ UserProfile model
- ✅ User model
- ✅ Django ORM
- ✅ DRF ViewSets and Serializers

---

## 13. QUICK REFERENCE: ALL WALLET REFERENCES

### Python/Django
- `promotions/models.py` - WalletTopUp, WithdrawalRequest, FacilitatorEarning (3 models)
- `promotions/views.py` - WalletTopUpViewSet, WithdrawalRequestViewSet (2 viewsets + methods)
- `promotions/serializers.py` - WalletTopUpSerializer, WithdrawalRequestSerializer
- `promotions/urls.py` - wallet-topups, withdrawals routes
- `promotions/dashboard_analytics.py` - available_balance calculation
- `accounts/models.py` - balance, total_earnings fields
- `accounts/serializers.py` - balance, total_earnings fields

### TypeScript/React
- `frontend/src/hooks/dashboardAnalytics.ts` - useFacilitatorAnalytics (returns available_balance)
- `frontend/src/hooks/usePromotions.ts` - availableBalance state
- `frontend/src/hooks/useWithdrawals.ts` - entire file
- `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx` - walletBalance (lines 87-90, 138, 144-145, 308-309, 627, 744, 767)

---

## 14. DOCUMENTATION FILES TO UPDATE

- `WALLET_TOPUP_QUICK_REFERENCE.md` - **DELETE (entire file)**
- `frontend/src/hooks/INTEGRATION_GUIDE.tsx` - Update if mentions wallet
- Any README files referencing wallet functionality

---

**END OF AUDIT REPORT**
