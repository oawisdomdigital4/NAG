# Wallet System Removal - Implementation Checklist

## Overview
Complete step-by-step guide to remove facilitator wallet, balance, earnings, and withdrawal functionality from the entire codebase.

---

## PHASE 1: DATABASE & BACKEND MODELS

### 1.1 Remove Wallet Models from Django
- [ ] **File:** `promotions/models.py`
  - [ ] Remove `FacilitatorEarning` class (lines ~253-263)
  - [ ] Remove `WithdrawalRequest` class (lines ~268-360)
  - [ ] Remove `WalletTopUp` class (lines ~362-430)
  - [ ] **Verify:** No orphaned imports after removal

- [ ] **File:** `accounts/models.py`
  - [ ] Remove field: `balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)` (line 58)
  - [ ] Remove field: `total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)` (line 60)
  - [ ] Remove comments referencing balance tracking (lines 57, 59)
  - [ ] **Verify:** UserProfile still has all required fields (full_name, avatar, etc.)

### 1.2 Create Migration
- [ ] Generate migration: `python manage.py makemigrations`
- [ ] Apply migration: `python manage.py migrate`
- [ ] Verify no errors in migration application
- [ ] **Backup database** before running migration

---

## PHASE 2: BACKEND SERIALIZERS & APIS

### 2.1 Remove Serializers
- [ ] **File:** `promotions/serializers.py`
  - [ ] Remove `WithdrawalRequestSerializer` class (lines ~14-53)
  - [ ] Remove `WalletTopUpSerializer` class (lines ~215-244)
  - [ ] Remove imports: `WithdrawalRequest`, `WalletTopUp`, `FacilitatorEarning`
  - [ ] Update imports to remove unused model references

### 2.2 Remove ViewSets
- [ ] **File:** `promotions/views.py`
  - [ ] Remove `WalletTopUpViewSet` class and all methods (entire class)
  - [ ] Remove `WithdrawalRequestViewSet` class and all methods (entire class)
  - [ ] Remove imports: `WalletTopUp`, `WithdrawalRequest` from models
  - [ ] Remove imports: `WalletTopUpSerializer`, `WithdrawalRequestSerializer`
  
  - [ ] In `SponsorCampaignViewSet.start_campaign()` method:
    - [ ] **KEEP** the campaign creation logic
    - [ ] **REMOVE** balance deduction code (lines ~122-127):
      ```python
      # REMOVE THIS:
      if status != 'draft' and budget > 0:
          updated = UserProfile.objects.filter(user=user, balance__gte=budget).update(balance=F('balance') - budget)
          if updated == 0:
              return Response({'error': 'Insufficient balance'}, status=402)
      ```
    - [ ] Campaigns can now be created at any budget level (no balance check)

### 2.3 Update URLs
- [ ] **File:** `promotions/urls.py`
  - [ ] Remove line: `router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawal')`
  - [ ] Remove line: `router.register(r'wallet-topups', WalletTopUpViewSet, basename='wallet-topup')`
  - [ ] Verify router still includes: `sponsor-campaigns`, `opportunities`

### 2.4 Update Analytics Endpoints
- [ ] **File:** `promotions/dashboard_analytics.py`
  - [ ] In `FacilitatorAnalyticsView.get()` method:
    - [ ] **REMOVE** lines 218-222 (available_balance calculation):
      ```python
      # REMOVE:
      try:
          profile = getattr(user, 'profile', None)
          balance = float(getattr(profile, 'balance', 0) or 0)
          total_earnings = float(getattr(profile, 'total_earnings', 0) or 0)
          payload['available_balance'] = balance + total_earnings
      except Exception:
          payload['available_balance'] = float(earnings.get('total_earnings') or 0)
      ```
    - [ ] Remove `available_balance` key from payload
  
  - [ ] Remove FacilitatorEarning imports if unused elsewhere
  - [ ] Verify response still includes: earning_trends, engagement_by_type, etc.

---

## PHASE 3: FRONTEND HOOKS

### 3.1 Update Analytics Hooks
- [ ] **File:** `frontend/src/hooks/useDashboardAnalytics.ts`
  - [ ] In `useFacilitatorAnalytics()` function:
    - [ ] Verify it still calls `/api/promotions/analytics/facilitator/`
    - [ ] Update type definition to remove `available_balance` field
    - [ ] Update response handling (if available_balance is removed from API)

### 3.2 Update usePromotions Hook
- [ ] **File:** `frontend/src/hooks/usePromotions.ts`
  - [ ] Remove line: `const [availableBalance, setAvailableBalance] = useState<number>(0);`
  - [ ] Remove balance calculation logic (lines ~35-40)
  - [ ] Remove from return: `availableBalance`
  - [ ] Update return type to exclude availableBalance

### 3.3 Delete useWithdrawals Hook
- [ ] **File:** `frontend/src/hooks/useWithdrawals.ts`
  - [ ] **DELETE ENTIRE FILE** (no longer needed)
  - [ ] Search codebase for imports of `useWithdrawals` and remove them

### 3.4 Update dashboardAnalytics Export
- [ ] **File:** `frontend/src/hooks/dashboardAnalytics.ts`
  - [ ] Verify file still exports: `useCorporateAnalytics`, `useFacilitatorAnalytics`, `useUserEngagementAnalytics`
  - [ ] No changes needed if exports are correct

---

## PHASE 4: FRONTEND PAGES & COMPONENTS

### 4.1 Update CampaignsPage
- [ ] **File:** `frontend/src/pages/dashboard/corporate/CampaignsPage.tsx`
  - [ ] **Line 10:** Remove or update import: `import { useFacilitatorAnalytics } from '../../../hooks/dashboardAnalytics';`
    - [ ] If still needed for other analytics, keep it
    - [ ] If ONLY used for wallet balance, remove import
  
  - [ ] **Line 47:** Remove or update:
    ```tsx
    // REMOVE:
    const { data: analytics } = useFacilitatorAnalytics(30);
    ```
  
  - [ ] **Lines 87-90:** Remove wallet balance calculation:
    ```tsx
    // REMOVE:
    const walletBalance = Number((analytics && (analytics as any).available_balance != null)
      ? (analytics as any).available_balance
      : ((user?.profile && (user.profile as any).balance) ?? 50000));
    ```
  
  - [ ] **Line 138:** Update `createCampaignWithStatus()` - remove balance validation:
    ```tsx
    // REMOVE:
    if (requireBalance && walletBalance < formData.budget) {
      showToast(`Insufficient wallet balance. Required: $${formData.budget}, Available: $${walletBalance.toFixed(2)}`, 'error');
      return;
    }
    ```
  
  - [ ] **Line 144:** Remove parameter `requireBalance = true` (make it `requireBalance = false` or remove checks)
  
  - [ ] **Lines 308-309:** Remove UI section displaying wallet balance:
    ```tsx
    {/* REMOVE THIS SECTION */}
    <p className="text-sm font-semibold opacity-90">Wallet Balance</p>
    <p className="text-2xl font-bold">${walletBalance.toFixed(2)}</p>
    ```
  
  - [ ] **Line 627:** Remove remaining balance calculation display:
    ```tsx
    // CHANGE:
    Amount: <strong>${formData.budget.toFixed(2)}</strong> | Remaining balance: <strong>${(walletBalance - formData.budget).toFixed(2)}</strong>
    // TO:
    Amount: <strong>${formData.budget.toFixed(2)}</strong>
    ```
  
  - [ ] **Line 744:** Remove balance info text:
    ```tsx
    // REMOVE:
    <p className="text-xs text-gray-600 mt-2">Minimum: $10.00 | Current balance: ${walletBalance.toFixed(2)}</p>
    ```
  
  - [ ] **Line 767:** Remove balance check from button disabled state:
    ```tsx
    // CHANGE FROM:
    disabled={!formData.title || !formData.description || walletBalance < formData.budget || isCreatingCampaign}
    // TO:
    disabled={!formData.title || !formData.description || isCreatingCampaign}
    ```

### 4.2 Search for Other Component References
- [ ] Search codebase for files importing/using wallet hooks:
  ```bash
  grep -r "useWithdrawals\|availableBalance\|wallet.*balance" frontend/src/
  ```
- [ ] Remove any other references to:
  - `useWithdrawals`
  - `availableBalance`
  - `walletBalance`
  - `wallet.*topup` (case-insensitive)

---

## PHASE 5: DOCUMENTATION & CLEANUP

### 5.1 Remove Documentation Files
- [ ] **File:** `WALLET_TOPUP_QUICK_REFERENCE.md`
  - [ ] DELETE ENTIRE FILE (no longer relevant)

- [ ] **File:** Any other wallet-related docs
  - [ ] Search for: `wallet`, `topup`, `withdrawal` in markdown files
  - [ ] Remove sections or delete files as appropriate

### 5.2 Update Main Documentation
- [ ] **File:** `README.md` (if mentions wallet features)
  - [ ] Remove wallet feature descriptions
  - [ ] Remove wallet API documentation
  - [ ] Update feature list

- [ ] **File:** `IMPLEMENTATION_STATUS.md` or similar
  - [ ] Remove wallet system from "Completed Features"
  - [ ] Add note: "Wallet/balance system removed - campaigns now freely created"

### 5.3 Search for Hard-Coded References
- [ ] Search for string literals:
  ```bash
  grep -r "wallet\|topup\|withdrawal\|available_balance\|total_earnings" . \
    --include="*.py" --include="*.tsx" --include="*.ts" \
    | grep -v node_modules | grep -v ".git"
  ```
- [ ] Remove or update any remaining references

---

## PHASE 6: TESTING & VALIDATION

### 6.1 Backend Testing
- [ ] Run Django migrations: `python manage.py migrate`
- [ ] Test campaign creation endpoint:
  ```bash
  POST /api/promotions/sponsor-campaigns/start_campaign/
  {
    "title": "Test Campaign",
    "description": "Test",
    "budget": 999999,  // Should work regardless of balance
    "status": "active"
  }
  ```
  - [ ] Verify campaign creates successfully **without balance deduction**

- [ ] Test analytics endpoint:
  ```bash
  GET /api/promotions/analytics/facilitator/?days=30
  ```
  - [ ] Verify `available_balance` is **NOT in response**
  - [ ] Verify other fields present: earning_trends, engagement_by_type, etc.

- [ ] Verify withdrawal endpoints return 404:
  ```bash
  GET /api/promotions/withdrawals/
  POST /api/promotions/wallet-topups/current_balance/
  ```

### 6.2 Frontend Testing
- [ ] Start dev server: `npm start` or `npm run dev`
- [ ] Navigate to Campaigns page
  - [ ] Verify no console errors about missing `useFacilitatorAnalytics`
  - [ ] Verify wallet balance section **not displayed**
  - [ ] Verify campaign creation form still works
  - [ ] Create a campaign with high budget (should work)
  - [ ] Verify no "Insufficient balance" errors

- [ ] Check browser console for warnings about undefined variables
  - [ ] Fix any references to removed hooks

### 6.3 Admin Dashboard Testing
- [ ] Login as admin
- [ ] Verify `/admin/promotions/` doesn't show Withdrawal/WalletTopUp models
- [ ] Verify UserProfile admin doesn't show balance/total_earnings fields
- [ ] Verify no broken admin links

### 6.4 API Testing (Postman/Curl)
- [ ] Test that removed endpoints return 404:
  ```bash
  curl -X GET http://localhost:8000/api/promotions/withdrawals/
  curl -X POST http://localhost:8000/api/promotions/wallet-topups/current_balance/
  ```
  - [ ] Expected: 404 Not Found

---

## PHASE 7: DATABASE CLEANUP (Optional but Recommended)

### 7.1 Archive Old Data (Recommended)
- [ ] Create backup tables:
  ```sql
  CREATE TABLE promotions_wallettopup_backup AS SELECT * FROM promotions_wallettopup;
  CREATE TABLE promotions_withdrawalrequest_backup AS SELECT * FROM promotions_withdrawalrequest;
  CREATE TABLE promotions_facilitatorearning_backup AS SELECT * FROM promotions_facilitatorearning;
  ```

### 7.2 Clean Up Orphaned Data
- [ ] After migration is applied, verify no wallet data remains:
  ```bash
  python manage.py dbshell
  SELECT COUNT(*) FROM promotions_wallettopup;  -- Should be 0 or table doesn't exist
  SELECT COUNT(*) FROM promotions_withdrawalrequest;  -- Should be 0 or table doesn't exist
  SELECT COUNT(*) FROM promotions_facilitatorearning;  -- Should be 0 or table doesn't exist
  ```

---

## PHASE 8: DEPLOYMENT CHECKLIST

### 8.1 Pre-Deployment
- [ ] Run full test suite: `python manage.py test`
- [ ] Run frontend build: `npm run build` (no errors)
- [ ] Code review: Verify all changes
- [ ] Database backup created
- [ ] Rollback plan documented

### 8.2 Deployment
- [ ] Merge to production branch
- [ ] Deploy backend code
- [ ] Run migrations in production: `python manage.py migrate`
- [ ] Verify migrations successful
- [ ] Deploy frontend code
- [ ] Clear browser cache / CDN cache
- [ ] Monitor error logs for issues

### 8.3 Post-Deployment
- [ ] Test endpoints in production
- [ ] Verify no 500 errors in logs
- [ ] Monitor user reports
- [ ] Verify campaigns still creatable
- [ ] Spot-check admin dashboard

---

## PHASE 9: DOCUMENTATION UPDATES

### 9.1 API Documentation
- [ ] Update API docs to remove:
  - `/api/promotions/wallet-topups/` endpoints
  - `/api/promotions/withdrawals/` endpoints
  - `available_balance` from FacilitatorAnalytics response

### 9.2 Code Documentation
- [ ] Update docstrings in remaining views
- [ ] Update type definitions in TypeScript
- [ ] Update README if wallet was documented

### 9.3 Developer Guide
- [ ] Update any developer guides mentioning wallet system
- [ ] Document new campaign creation (no balance checks)

---

## PHASE 10: FINAL VERIFICATION

- [ ] All removed imports resolved
- [ ] No broken links in documentation
- [ ] No TypeScript compilation errors
- [ ] No Python syntax errors
- [ ] All tests passing
- [ ] No wallet-related data in database
- [ ] Analytics endpoint responds without available_balance
- [ ] Campaign creation works with any budget amount
- [ ] Frontend displays without wallet UI sections
- [ ] Admin dashboard clean (no wallet models)

---

## QUICK REMOVAL COMMANDS (Reference)

```bash
# Find all wallet references
grep -r "wallet\|topup\|withdrawal\|available_balance" . \
  --include="*.py" --include="*.tsx" --include="*.ts" \
  | grep -v ".git" | grep -v "node_modules"

# Count references by file type
grep -r "available_balance" --include="*.py" . | wc -l
grep -r "wallet" --include="*.tsx" frontend/ | wc -l

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Build frontend
npm run build

# Run tests
python manage.py test
npm test
```

---

## RISKS & MITIGATION

| Risk | Mitigation |
|------|-----------|
| Data loss | Create full database backup before migrations |
| Broken APIs | Test all endpoints before and after removal |
| Frontend crashes | Test in dev environment, clear cache |
| Admin issues | Verify admin models correctly removed |
| User impact | Inform users that balance checks removed |
| Deployment failure | Have rollback plan with backup data |

---

## SUCCESS CRITERIA

✅ All wallet models removed  
✅ All wallet endpoints removed (404 on access)  
✅ All wallet hooks removed  
✅ CampaignsPage displays without wallet UI  
✅ Campaigns creatable without balance checks  
✅ Analytics endpoint returns without available_balance  
✅ No console errors in frontend  
✅ No 500 errors in backend logs  
✅ Database migrations successful  
✅ All tests passing  
✅ Documentation updated  

---

**Total Estimated Files to Modify:** 13  
**Total Estimated Lines to Remove:** ~1,500  
**Estimated Time:** 2-3 hours  

