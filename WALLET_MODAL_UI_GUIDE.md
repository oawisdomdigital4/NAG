# Wallet Recharge Modal - UI/UX Guide

## Visual Structure

```
┌─────────────────────────────────────────────────────────┐
│                    MODAL OVERLAY                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │  🔵 Insufficient Balance                     ✕   │  │
│  ├───────────────────────────────────────────────────┤  │
│  │                                                   │  │
│  │  Current balance:     $10.00                     │  │
│  │  Required amount:     $40.00                     │  │
│  │  ─────────────────────────                       │  │
│  │  Shortfall:           $30.00                     │  │
│  │                                                   │  │
│  │  Recharge Amount                                 │  │
│  │  ┌─────────────────────────────────────────┐    │  │
│  │  │ $ 40.00                                 │    │  │
│  │  └─────────────────────────────────────────┘    │  │
│  │  Minimum: $30.00 to complete enrollment        │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────┐    │  │
│  │  │ New balance after recharge:             │    │  │
│  │  │ $50.00                                  │    │  │
│  │  └─────────────────────────────────────────┘    │  │
│  │                                                   │  │
│  │  Payment Method                                 │  │
│  │  ○ 💳 Credit/Debit Card                        │  │
│  │  ○ 🅿️  PayPal                                  │  │
│  │  ○ 🏦 Bank Transfer                            │  │
│  │                                                   │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ [Cancel]                [💳 Recharge $40.00]    │  │
│  │                                                   │  │
│  │ 🔒 Your payment information is secure...         │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Color Scheme

| Element | Color | RGB |
|---------|-------|-----|
| Header Icon Background | Light Blue | `#dbeafe` |
| Header Icon | Brand Blue | `#0066ff` |
| Balance Text (Current) | Gray 600 | `#4b5563` |
| Balance Amount (Required) | Red 600 | `#dc2626` |
| Balance Box Background | Gray 50 | `#f9fafb` |
| Preview Box Background | Green 50 | `#f0fdf4` |
| Preview Amount | Green 700 | `#15803d` |
| Cancel Button Border | Gray 300 | `#d1d5db` |
| Cancel Button Text | Gray 700 | `#374151` |
| Recharge Button | Brand Blue | `#0066ff` |
| Recharge Button Hover | Blue 700 | `#1e40af` |
| Footer Background | Blue 50 | `#eff6ff` |

## Interactive States

### Default State
```
Current balance: $10.00
Recharge Amount: $40.00 (pre-filled)
New balance preview: $50.00
Buttons: Cancel [enabled] | Recharge $40.00 [enabled]
```

### User Adjusts Amount
```
User types: $100
New balance preview: $110.00 (real-time update)
Recharge button text: "Recharge $100.00"
```

### Processing State
```
Recharge button: [spinner] Processing...
Cancel button: [disabled]
Input fields: [disabled]
Payment methods: [disabled]
```

### After Success
```
Alert: "Recharge successful! Please try enrolling again."
Modal closes
User can now click "Enroll Now" with new balance
```

## Responsive Behavior

### Desktop (1024px+)
- Modal: 500px width, centered
- All fields full width
- Payment methods as vertical stack

### Tablet (768px - 1024px)
- Modal: 90% width, max-width 500px
- Same layout, slightly adjusted padding

### Mobile (< 768px)
- Modal: 95% width with 8px horizontal padding
- Buttons full width, stacked vertically
- Slightly reduced font sizes
- Touch-friendly padding on interactive elements

## Accessibility Features

### Keyboard Navigation
- Tab: Move between fields
- Shift+Tab: Move backwards
- Enter: Submit (Recharge button)
- Esc: Close modal (cancel)

### Screen Reader Support
- Modal dialog role
- ARIA-labels on all inputs
- Button purpose clearly stated
- Error messages announced

### Visual Accessibility
- High contrast text (WCAG AA compliant)
- Large touch targets (44px minimum)
- Clear visual feedback on focus
- Icon + text combinations

## Animation Details

### Modal Entry
```css
animation: fadeIn 0.2s ease-out
opacity: 0 → 1
```

### Button Hover
```css
transition: all 0.3s ease
background-color: change
box-shadow: increase
```

### Input Focus
```css
ring-2 ring-brand-blue
border-color: transparent
```

## Error Scenarios

### Invalid Amount
```
User enters: $5 (less than $30 shortfall)
Field shows: Red border
Message: "Minimum: $30.00"
Submit button: [disabled]
```

### Network Error
```
Show: "Recharge failed. Please try again."
Button state: Back to enabled
User can retry
```

### Payment Declined
```
Alert: "Payment declined. Please try another method."
Modal stays open
User can change method or amount
```

## Loading States

### Fetching Balance
```
Sidebar shows: [skeleton loader]
"Loading wallet..."
Recharge button: [disabled]
```

### Processing Recharge
```
Button text: [spinner icon] Processing...
Button color: Disabled (gray)
Modal backdrop: More opaque
All inputs: Disabled
```

## Success Flow

1. User sees enrollment error
2. Modal pops up with current: $10, required: $40
3. Default recharge amount: $40
4. New balance preview shows: $50
5. User selects payment method: Credit Card
6. User clicks "Recharge $40.00"
7. Button shows loading spinner
8. Backend processes payment
9. Alert: "Recharge successful!"
10. Modal closes
11. User retries enrollment
12. Enrollment succeeds with new balance

## Edge Cases Handled

### Exactly $0 Balance
```
Current: $0.00
Required: $40.00
Shortfall: $40.00
Min recharge: $40.00 (full course price)
```

### Very Close ($39.99)
```
Current: $39.99
Required: $40.00
Shortfall: $0.01
Min recharge: $0.01
```

### Large Amounts
```
Current: $1,000
Course: $10,000
Shortfall: $9,000
```

## Text Content

### Header
- Title: "Insufficient Balance"
- Icon: Warning/Alert icon (blue)
- Close: X button

### Body
- "Current balance: $X.XX"
- "Required amount: $X.XX"
- "Shortfall: $X.XX"
- "Recharge Amount" (label)
- "Minimum: $X.XX to complete enrollment" (hint)
- "New balance after recharge: $X.XX"
- "Payment Method" (label)
- Payment options with emoji

### Actions
- Cancel: "Cancel"
- Recharge: "💳 Recharge $X.XX"

### Footer
- Security: "🔒 Your payment information is secure and encrypted. We never store your card details."

## Mobile Considerations

### Touch Targets
- Minimum 44x44px for all buttons
- Larger radio button hit area
- Increased padding around inputs

### Keyboard
- Numeric keyboard for amount field
- No accidental double-taps
- Clear focus indicators

### Network
- Handles slow connections gracefully
- Shows processing state clearly
- Allows retry on failure
