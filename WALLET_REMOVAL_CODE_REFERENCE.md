# Wallet System - Exact Code Removal Reference

This document shows the EXACT code sections to remove from each file.

---

## FILE 1: promotions/models.py

### REMOVE: FacilitatorEarning Model (Lines ~253-263)

```python
# DELETE THIS ENTIRE CLASS:
class FacilitatorEarning(models.Model):
    """Track earnings for facilitators"""
    facilitator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=100)  # e.g., 'course_sale', 'sponsorship'
    description = models.TextField(blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.facilitator.username} - {self.amount} ({self.source})"
```

### REMOVE: WithdrawalRequest Model (Lines ~268-360)

```python
# DELETE THIS ENTIRE CLASS:
class WithdrawalRequest(models.Model):
    """Track withdrawal requests from facilitators"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]

    facilitator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='promotions_withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='promotions_processed_withdrawals'
    )

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.facilitator.username} - {self.amount} ({self.status})"

    def process(self, status, processed_by, notes=''):
        """Process the withdrawal request"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Processing withdrawal {self.id}: changing to {status}")
        
        self.status = status
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
        logger.info(f"Withdrawal {self.id} saved with status {status}")
        
        # If approved or completed, deduct from user's balance
        if status in ['approved', 'completed']:
            logger.info(f"Attempting to deduct balance for withdrawal {self.id}")
            profile = getattr(self.facilitator, 'profile', None)
            if profile:
                logger.info(f"Found profile for {self.facilitator.username}. Current balance: {profile.balance}, total_earnings: {profile.total_earnings}")
                
                # Deduct the withdrawal amount from the available balance (balance + total_earnings)
                # First deduct from total_earnings, then from balance
                withdrawal_amount = Decimal(str(self.amount))
                total_earnings = Decimal(str(profile.total_earnings or 0))
                balance = Decimal(str(profile.balance or 0))
                
                # Deduct from total_earnings first
                if total_earnings >= withdrawal_amount:
                    new_total_earnings = total_earnings - withdrawal_amount
                    new_balance = balance
                    logger.info(f"Deducting {withdrawal_amount} from total_earnings: {total_earnings} -> {new_total_earnings}")
                else:
                    # If not enough in total_earnings, deduct the rest from balance
                    amount_to_deduct_from_balance = withdrawal_amount - total_earnings
                    new_total_earnings = Decimal('0')
                    new_balance = max(balance - amount_to_deduct_from_balance, Decimal('0'))
                    logger.info(f"Deducting {total_earnings} from total_earnings and {amount_to_deduct_from_balance} from balance: balance {balance} -> {new_balance}")
                
                profile.total_earnings = new_total_earnings
                profile.balance = new_balance
                profile.save()
                logger.info(f"Profile saved. New balance: {profile.balance}, new total_earnings: {profile.total_earnings}")
            else:
                logger.error(f"No profile found for user {self.facilitator.id}")
            
            # Mark related earnings as paid
            updated = FacilitatorEarning.objects.filter(
                facilitator=self.facilitator,
                is_paid=False,
                amount__lte=self.amount
            ).update(is_paid=True)
            logger.info(f"Marked {updated} earnings as paid for withdrawal {self.id}")
        else:
            logger.info(f"Status {status} is not approved or completed, skipping balance deduction")
```

### REMOVE: WalletTopUp Model (Lines ~362-430)

```python
# DELETE THIS ENTIRE CLASS:
class WalletTopUp(models.Model):
    """Track wallet top-up transactions for promotions budget"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_topups')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)  # e.g., 'credit_card', 'bank_transfer', 'paypal'
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"

    def mark_completed(self):
        """Mark the top-up as completed and add funds to user wallet"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Marking wallet top-up {self.id} as completed")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Add amount to user's wallet balance
        profile = getattr(self.user, 'profile', None)
        if profile:
            profile.balance = (profile.balance or Decimal('0')) + Decimal(str(self.amount))
            profile.save()
            logger.info(f"Added ${self.amount} to {self.user.username}'s wallet. New balance: ${profile.balance}")
        else:
            logger.error(f"No profile found for user {self.user.id}")

    def mark_failed(self, error_message=''):
        """Mark the top-up as failed"""
        self.status = 'failed'
        if error_message:
            self.notes = error_message
        self.save()
```

### REMOVE: Imports in promotions/models.py

At the top of the file, look for and REMOVE:
```python
# These imports can be removed if not used elsewhere:
from .models import SponsorCampaign, EngagementLog, WithdrawalRequest, WalletTopUp
from .models import FacilitatorEarning
```

---

## FILE 2: accounts/models.py

### REMOVE: Balance Fields from UserProfile (Lines 57-60)

```python
# REMOVE THESE LINES:
    # Track available balance for payouts (editable via admin)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Track total earnings for facilitators (editable via admin for manual adjustments)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

# RESULT: UserProfile class should go directly from:
    avatar_url = models.CharField(max_length=512, blank=True, default='')
    portfolio_url = models.CharField(max_length=512, blank=True, default='')
# (no balance/earnings fields)
```

---

## FILE 3: promotions/serializers.py

### REMOVE: WithdrawalRequestSerializer (Lines 14-53)

```python
# DELETE THIS ENTIRE CLASS:
class WithdrawalRequestSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'amount', 'status', 'requested_at',
            'processed_at', 'total_earnings', 'pending_amount',
            'bank_name', 'account_number', 'account_name', 'notes'
        ]
        read_only_fields = ('status', 'processed_at', 'created_at', 'id')
    
    def get_total_earnings(self, obj):
        return FacilitatorEarning.objects.filter(
            facilitator=obj.facilitator
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_pending_amount(self, obj):
        return FacilitatorEarning.objects.filter(
            facilitator=obj.facilitator,
            is_paid=False
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def validate_amount(self, value):
        """Validate that withdrawal amount is positive and within limits"""
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be positive")
        if value < 50:
            raise serializers.ValidationError("Minimum withdrawal amount is $50")
        
        # Get the user from the request context
        request = self.context.get('request')
        if request and request.user:
            profile = getattr(request.user, 'profile', None)
            if profile:
                available_balance = float(profile.balance or 0) + float(profile.total_earnings or 0)
                if value > available_balance:
                    raise serializers.ValidationError(
                        f"Insufficient available balance. Available: ${available_balance:.2f}"
                    )
        return value
```

### REMOVE: WalletTopUpSerializer (Lines 215-244)

```python
# DELETE THIS ENTIRE CLASS:
class WalletTopUpSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WalletTopUp
        fields = [
            'id', 'user_id', 'amount', 'status', 'payment_method',
            'transaction_id', 'payment_reference', 'notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ('id', 'user_id', 'status', 'transaction_id', 
                           'created_at', 'updated_at', 'completed_at')

    def validate_amount(self, value):
        """Validate that top-up amount is reasonable"""
        from decimal import Decimal
        if value <= 0:
            raise serializers.ValidationError("Top-up amount must be positive")
        if value < Decimal('1.00'):
            raise serializers.ValidationError("Minimum top-up amount is $1.00")
        if value > Decimal('10000.00'):
            raise serializers.ValidationError("Maximum top-up amount is $10,000")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)
```

### REMOVE: Imports in promotions/serializers.py

```python
# At the top of the file, REMOVE or UPDATE these imports:
from .models import (
    WithdrawalRequest,      # REMOVE
    FacilitatorEarning,     # REMOVE
    WalletTopUp,            # REMOVE
    ...other models...
)

from .serializers import (
    WithdrawalRequestSerializer,  # REMOVE
    WalletTopUpSerializer,        # REMOVE
    ...other serializers...
)
```

---

## FILE 4: promotions/views.py

### REMOVE: Imports

```python
# REMOVE these lines:
from .models import SponsorCampaign, EngagementLog, WithdrawalRequest, WalletTopUp
from .serializers import (
    ...
    WithdrawalRequestSerializer,
    WalletTopUpSerializer,
)
```

### REMOVE: WithdrawalRequestViewSet (entire class)

```python
# DELETE THIS ENTIRE CLASS:
class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Admin/staff can see all withdrawals, regular users can only see their own
        if user.is_staff or user.is_superuser:
            return WithdrawalRequest.objects.all()
        # promotions WithdrawalRequest stores facilitator as the user field
        return WithdrawalRequest.objects.filter(facilitator=user)

    def perform_create(self, serializer):
        serializer.save(facilitator=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a withdrawal request and deduct from user's balance"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('approved', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error approving withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a withdrawal request"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('rejected', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rejecting withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def complete(self, request, pk=None):
        """Mark a withdrawal as completed and deduct from user's balance"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('completed', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def record_impression(self, request, pk=None):
        """Record an impression for a sponsor campaign (public endpoint)."""
        campaign = self.get_object()
        try:
            SponsorCampaign.objects.filter(id=campaign.id).update(impression_count=F('impression_count') + 1)
            EngagementLog.objects.create(
                user=request.user if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False) else None,
                action_type='view',
                post=campaign.sponsored_post if hasattr(campaign, 'sponsored_post') else None,
                metadata={'campaign_id': campaign.id},
            )
        except Exception:
            return Response({'detail': 'failed to record impression'}, status=500)
        return Response({'status': 'impression recorded'})
```

### REMOVE: WalletTopUpViewSet (entire class)

```python
# DELETE THIS ENTIRE CLASS:
class WalletTopUpViewSet(viewsets.ModelViewSet):
    """ViewSet for managing wallet top-ups"""
    serializer_class = WalletTopUpSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Admin/staff can see all top-ups, regular users can only see their own
        if user.is_staff or user.is_superuser:
            return WalletTopUp.objects.all()
        return WalletTopUp.objects.filter(user=user)

    def perform_create(self, serializer):
        """Create a new wallet top-up request"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def initiate_payment(self, request):
        """Initiate a wallet top-up payment
        
        Expected POST data:
        {
            "amount": 100.00,
            "payment_method": "credit_card"
        }
        """
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'credit_card')
        
        if not amount:
            return Response(
                {'detail': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'detail': 'Amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if amount > Decimal('10000.00'):
                return Response(
                    {'detail': 'Maximum top-up amount is $10,000'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the top-up record in pending status
        topup = WalletTopUp.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            status='processing'
        )
        
        serializer = self.get_serializer(topup)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def complete(self, request, pk=None):
        """Admin action to mark a top-up as completed and add funds to wallet"""
        topup = self.get_object()
        try:
            topup.mark_completed()
            serializer = self.get_serializer(topup)
            return Response(
                {
                    'detail': f'Top-up of ${topup.amount} completed successfully',
                    'topup': serializer.data,
                    'new_balance': float(topup.user.profile.balance) if hasattr(topup.user, 'profile') else 0
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing top-up {pk}: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def fail(self, request, pk=None):
        """Admin action to mark a top-up as failed"""
        topup = self.get_object()
        error_message = request.data.get('error_message', '')
        try:
            topup.mark_failed(error_message)
            serializer = self.get_serializer(topup)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error failing top-up {pk}: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def current_balance(self, request):
        """Get the current wallet balance for the user"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response(
                {'detail': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'balance': float(profile.balance or 0),
            'total_earnings': float(profile.total_earnings or 0),
            'available': float((profile.balance or 0) + (profile.total_earnings or 0))
        }, status=status.HTTP_200_OK)
```

### MODIFY: SponsorCampaignViewSet.start_campaign() method

```python
# FIND THIS SECTION (around line 122-127):
@action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
def start_campaign(self, request):
    """Start a new campaign for the user"""
    user = request.user
    
    # ... validation code ...
    
    # REMOVE THIS ENTIRE BLOCK:
    with transaction.atomic():
        if status != 'draft' and budget > 0:
            # Attempt to atomically decrement user profile balance
            updated = UserProfile.objects.filter(user=user, balance__gte=budget).update(balance=F('balance') - budget)
            if updated == 0:
                return Response({'error': 'Insufficient balance'}, status=402)

        # Create campaign linked to the post
        campaign = SponsorCampaign.objects.create(
            ...

    # REPLACE WITH:
    with transaction.atomic():
        # Create campaign linked to the post (no balance deduction)
        campaign = SponsorCampaign.objects.create(
            ...
```

---

## FILE 5: promotions/urls.py

### REMOVE: ViewSet registrations

```python
# REMOVE THESE LINES:
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawal')
router.register(r'wallet-topups', WalletTopUpViewSet, basename='wallet-topup')

# Also remove their imports:
from .views import (
    ...
    WithdrawalRequestViewSet,
    WalletTopUpViewSet,
)
```

---

## FILE 6: promotions/dashboard_analytics.py

### REMOVE: available_balance calculation from FacilitatorAnalyticsView (Lines 218-222)

```python
# IN FacilitatorAnalyticsView.get() method, REMOVE:
        # Expose available balance: sum of balance and total_earnings (total_earnings is part of available balance)
        try:
            profile = getattr(user, 'profile', None)
            balance = float(getattr(profile, 'balance', 0) or 0) if profile and getattr(profile, 'balance', None) is not None else 0.0
            total_earnings = float(getattr(profile, 'total_earnings', 0) or 0) if profile and getattr(profile, 'total_earnings', None) is not None else float(earnings.get('total_earnings') or 0)
            payload['available_balance'] = balance + total_earnings
        except Exception:
            payload['available_balance'] = float(earnings.get('total_earnings') or 0)

# Also ensure the payload definition doesn't include it:
        payload = {
            'total_earnings': profile_total_earnings if profile_total_earnings is not None else float(earnings.get('total_earnings') or 0),
            'total_students': 0,
            'avg_rating': 0.0,
            'total_courses': 0,
            'earning_trends': [],
            'enrollment_trends': [],
            'course_performance': [],
            'rating_distribution': [],
            'engagement_by_type': [],
            'period_days': days,
            'growth_stats': {
                'earnings_growth': '',
                'student_growth': '',
                'rating_change': '',
                'course_growth': ''
            }
        }
        # Don't add 'available_balance' key
```

---

## FILE 7: accounts/serializers.py

### REMOVE: balance and total_earnings from field lists

```python
# FIND classes that reference balance/total_earnings:
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            ...,
            'balance',          # REMOVE
            'total_earnings',   # REMOVE
            ...
        ]

# Also in any other serializers that expose these fields
```

---

## FILE 8: frontend/src/hooks/usePromotions.ts

### REMOVE: availableBalance state and logic

```typescript
// REMOVE THIS:
  const [availableBalance, setAvailableBalance] = useState<number>(0);

// REMOVE THIS FROM load() function:
      const balance = (analyticsRes && (analyticsRes.available_balance || analyticsRes.available_balance === 0)) ? Number(analyticsRes.available_balance) : 0;
      setAvailableBalance(balance);

// REMOVE FROM return statement:
    availableBalance,
```

---

## FILE 9: frontend/src/hooks/useWithdrawals.ts

### DELETE: Entire file (no longer needed)

```bash
rm frontend/src/hooks/useWithdrawals.ts
```

Then search for any imports:
```bash
grep -r "useWithdrawals" frontend/src/
```
And remove any `import { useWithdrawals }` statements

---

## FILE 10: frontend/src/pages/dashboard/corporate/CampaignsPage.tsx

### REMOVE: Analytics import and usage

Line 10: Remove if ONLY used for wallet balance:
```typescript
// REMOVE (or keep if used for other analytics):
import { useFacilitatorAnalytics } from '../../../hooks/dashboardAnalytics';
```

Line 47: Remove the hook call:
```typescript
// REMOVE:
const { data: analytics } = useFacilitatorAnalytics(30);
```

### REMOVE: Wallet balance calculation (Lines 87-90)

```typescript
// REMOVE THESE LINES:
  // Get wallet balance from analytics (if available) or user profile (same as navbar)
  const walletBalance = Number((analytics && (analytics as any).available_balance != null)
    ? (analytics as any).available_balance
    : ((user?.profile && (user.profile as any).balance) ?? 50000));
```

### MODIFY: createCampaignWithStatus function (Line 138-146)

```typescript
// CHANGE FROM:
  const createCampaignWithStatus = async (status: string, requireBalance = true) => {
    // ...validation...
    
    if (requireBalance && walletBalance < formData.budget) {
      showToast(`Insufficient wallet balance. Required: $${formData.budget}, Available: $${walletBalance.toFixed(2)}`, 'error');
      return;
    }

// TO:
  const createCampaignWithStatus = async (status: string) => {
    // ...validation...
    // No balance check needed
```

### REMOVE: Wallet balance UI section (Lines 308-309)

```typescript
// REMOVE THIS JSX SECTION:
              <p className="text-sm font-semibold opacity-90">Wallet Balance</p>
              <p className="text-2xl font-bold">${walletBalance.toFixed(2)}</p>
```

### MODIFY: Display remaining balance (Line 627)

```typescript
// CHANGE FROM:
                    Amount: <strong>${formData.budget.toFixed(2)}</strong> | Remaining balance: <strong>${(walletBalance - formData.budget).toFixed(2)}</strong>

// TO:
                    Amount: <strong>${formData.budget.toFixed(2)}</strong>
```

### REMOVE: Balance info text (Line 744)

```typescript
// REMOVE:
                  <p className="text-xs text-gray-600 mt-2">Minimum: $10.00 | Current balance: ${walletBalance.toFixed(2)}</p>
```

### MODIFY: Button disabled state (Line 767)

```typescript
// CHANGE FROM:
                  disabled={!formData.title || !formData.description || walletBalance < formData.budget || isCreatingCampaign}

// TO:
                  disabled={!formData.title || !formData.description || isCreatingCampaign}
```

---

## FILE 11: WALLET_TOPUP_QUICK_REFERENCE.md

```bash
# DELETE ENTIRE FILE:
rm WALLET_TOPUP_QUICK_REFERENCE.md
```

---

## SUMMARY: FILES AFFECTED

| File | Action | Lines | Complexity |
|------|--------|-------|------------|
| promotions/models.py | Delete 3 classes | ~180 | High |
| accounts/models.py | Delete 2 fields | 2 | Low |
| promotions/serializers.py | Delete 2 classes | ~30 | Low |
| promotions/views.py | Delete 2 classes, modify 1 method | ~120 | High |
| promotions/urls.py | Delete 2 registrations | 2 | Low |
| promotions/dashboard_analytics.py | Delete 6 lines | 6 | Low |
| accounts/serializers.py | Update 2+ serializers | ~5 | Low |
| frontend hooks | Modify/delete 3 files | ~20 | Low |
| CampaignsPage.tsx | Modify 8+ locations | ~40 | Medium |
| WALLET_TOPUP_QUICK_REFERENCE.md | Delete | All | - |

**Total Lines to Remove:** ~400-500  
**Total Files Modified:** 11

