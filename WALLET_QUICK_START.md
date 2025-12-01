# Wallet System Removal - Quick Start Guide

**Quick Reference | One-Page Overview**

---

## 📋 What's Being Removed

- ❌ Wallet top-up system
- ❌ Withdrawal requests
- ❌ Balance/earnings tracking
- ❌ Campaign budget validation
- ✅ Campaigns can be created without restrictions

---

## 🎯 Quick File List

### Files to DELETE Entirely
```
frontend/src/hooks/useWithdrawals.ts
WALLET_TOPUP_QUICK_REFERENCE.md
```

### Files to MODIFY (remove classes/methods)
```
promotions/models.py              → 3 classes (180 lines)
promotions/views.py               → 2 classes + 1 method (120 lines)
promotions/serializers.py         → 2 classes (30 lines)
accounts/models.py                → 2 fields (2 lines)
promotions/urls.py                → 2 registrations (2 lines)
promotions/dashboard_analytics.py → 1 calculation (6 lines)
```

### Files to UPDATE (minor changes)
```
frontend/src/hooks/usePromotions.ts                      → Remove balance state
frontend/src/pages/dashboard/corporate/CampaignsPage.tsx → Remove 8 UI sections
accounts/serializers.py                                   → Remove field references
```

---

## ⚡ 5-Minute Removal Process

### Step 1: Backend Models (5 min)
```bash
# Edit: promotions/models.py
# DELETE these classes:
# - FacilitatorEarning (lines ~253-263)
# - WithdrawalRequest (lines ~268-360)
# - WalletTopUp (lines ~362-430)

# Edit: accounts/models.py
# DELETE these fields from UserProfile:
# - balance
# - total_earnings
```

### Step 2: Backend Views (5 min)
```bash
# Edit: promotions/views.py
# DELETE:
# - WalletTopUpViewSet (entire class)
# - WithdrawalRequestViewSet (entire class)

# MODIFY: SponsorCampaignViewSet.start_campaign()
# Remove balance deduction logic (lines ~122-127)

# Edit: promotions/urls.py
# DELETE:
# - router.register(r'wallet-topups', ...)
# - router.register(r'withdrawals', ...)
```

### Step 3: Serializers (2 min)
```bash
# Edit: promotions/serializers.py
# DELETE:
# - WithdrawalRequestSerializer (lines 14-53)
# - WalletTopUpSerializer (lines 215-244)

# Edit: accounts/serializers.py
# Remove 'balance' and 'total_earnings' from field lists
```

### Step 4: Analytics (1 min)
```bash
# Edit: promotions/dashboard_analytics.py
# In FacilitatorAnalyticsView.get(), REMOVE:
# - available_balance calculation (lines 218-222)
```

### Step 5: Frontend (3 min)
```bash
# Delete file:
rm frontend/src/hooks/useWithdrawals.ts

# Edit: frontend/src/hooks/usePromotions.ts
# Remove: availableBalance state

# Edit: frontend/src/pages/dashboard/corporate/CampaignsPage.tsx
# Remove 8 wallet UI sections:
# - Line 10: useFacilitatorAnalytics import
# - Line 47: Hook call
# - Line 87-90: walletBalance calculation
# - Line 138-146: Balance validation
# - Line 308-309: Wallet Balance display
# - Line 627: Remaining balance
# - Line 744: Minimum balance info
# - Line 767: Button disabled state
```

---

## 🔍 Search & Find Commands

```bash
# Find all wallet references
grep -rn "wallet\|topup\|withdrawal\|available_balance" . \
  --include="*.py" --include="*.tsx" --include="*.ts" \
  | grep -v node_modules | grep -v ".git"

# Find in specific directories
grep -rn "balance\|earnings" promotions/ accounts/
grep -rn "useFacilitatorAnalytics\|walletBalance" frontend/

# Count occurrences
grep -r "available_balance" --include="*.py" . | wc -l
grep -r "wallet" --include="*.tsx" frontend/ | wc -l
```

---

## ✅ Post-Removal Verification

### Backend Check
```bash
# Should return 404
curl http://localhost:8000/api/promotions/withdrawals/
curl http://localhost:8000/api/promotions/wallet-topups/

# Should work (no balance error)
curl -X POST http://localhost:8000/api/promotions/sponsor-campaigns/start_campaign/ \
  -d '{"title":"Test","budget":999999}' \
  -H "Content-Type: application/json"

# Should NOT include available_balance
curl http://localhost:8000/api/promotions/analytics/facilitator/
```

### Frontend Check
```bash
npm run build
# Should complete with no errors

# In browser console:
# Should be no errors about walletBalance or useWithdrawals
```

### Database Check
```bash
python manage.py migrate
# Should run successfully

python manage.py dbshell
SELECT * FROM accounts_userprofile LIMIT 1;
# Should NOT have balance or total_earnings columns
```

---

## 🚨 Common Mistakes

| ❌ Mistake | ✅ Solution |
|-----------|-----------|
| Deleting entire models.py | Only delete the 3 classes, keep everything else |
| Not updating imports | Search for "WithdrawalRequest, WalletTopUp" imports |
| Leaving balance in serializers | Check accounts/serializers.py too |
| Forgetting to remove from urls.py | Routes will cause 404 AttributeErrors |
| Not clearing browser cache | Hard refresh (Ctrl+F5) after frontend changes |

---

## 📊 Removal Stats

```
Total files modified:     11
Total files deleted:      2
Total classes removed:    5
Total fields removed:     2
Total endpoints removed:  15+
Lines of code removed:    ~400-500
Estimated time:           20-30 minutes
Risk level:               LOW ✅
```

---

## 🔄 Rollback Plan

If something breaks:

```bash
# Revert last commit
git revert HEAD

# Or restore database from backup
pg_restore -d myproject backup_before_removal.dump

# Or undo migration
python manage.py migrate promotions 0001_initial
```

---

## 📝 Checklist (Copy & Paste)

```
Backend:
- [ ] Removed 3 models from promotions/models.py
- [ ] Removed 2 fields from accounts/models.py
- [ ] Removed 2 serializers from promotions/serializers.py
- [ ] Removed 2 viewsets from promotions/views.py
- [ ] Modified start_campaign method (removed balance check)
- [ ] Updated URLs (removed 2 registrations)
- [ ] Updated dashboard_analytics (removed available_balance)
- [ ] Updated accounts/serializers.py

Frontend:
- [ ] Deleted useWithdrawals.ts
- [ ] Updated usePromotions.ts (removed balance state)
- [ ] Updated CampaignsPage.tsx (8 locations removed)
- [ ] Removed useFacilitatorAnalytics import (if only used for wallet)

Cleanup:
- [ ] Deleted WALLET_TOPUP_QUICK_REFERENCE.md
- [ ] Verified no broken imports
- [ ] Ran npm build (no errors)
- [ ] Ran migrations (no errors)
- [ ] Tested campaign creation (no balance errors)
- [ ] Tested analytics endpoint (no available_balance)
```

---

## 📞 If Something Goes Wrong

### Error: "Module not found: WithdrawalRequest"
→ Check promotions/views.py line 7, remove import

### Error: "Field 'balance' does not exist"
→ Check accounts/models.py, verify field removed

### Error: "No module named 'WalletTopUpViewSet'"
→ Check promotions/urls.py, verify routes removed

### Error: "TypeError: walletBalance is undefined"
→ Check CampaignsPage.tsx, verify all 8 sections removed

### Error: Migration fails
→ Run: `python manage.py migrate --fake`

---

## 📚 Full Documentation

- **WALLET_SYSTEM_COMPREHENSIVE_AUDIT.md** - Complete system analysis
- **WALLET_REMOVAL_IMPLEMENTATION_CHECKLIST.md** - Detailed step-by-step guide
- **WALLET_REMOVAL_CODE_REFERENCE.md** - Exact code to delete
- **WALLET_SEARCH_INDEX.md** - All references indexed

---

## 🎓 Key Points

1. **No data migration needed** - Can just delete models
2. **Campaigns still work** - Just without balance validation
3. **Users unaffected** - No account changes needed
4. **Admin dashboard** - Will auto-clean when models deleted
5. **Deployment safe** - Low-risk isolated removal

---

**Ready to remove? Start with Step 1 above! 🚀**

