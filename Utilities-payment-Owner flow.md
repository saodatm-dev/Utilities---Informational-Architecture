# Utilities Payment — Owner Payment User Flow & API Design

> **Module:** `utility` (extends `building` module)  
> **Actor:** Owner / Agent (`typ: "Owner"` or `typ: "Agent"` in JWT)  
> **Integration:** Paynet (utility aggregator, 390+ providers)  
> **Payment Method:** Paynet → Direct payment to provider via Paynet Aggregator  
> **Related:** [Tenant Utilities Flow](./utilities-payment-userflow.md) | [Owner Management Flow](./Utilities%20-%20Business%20Owner.md)

---

## Design Decisions (Confirmed)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Scope | Owner pays for utility accounts where `responsibility = Owner`, or voluntarily pays tenant's overdue bills |
| 2 | Payment trigger | Bills appear in Owner's Payment Queue when responsibility is set to "Owner" or when Owner chooses to cover a tenant's debt |
| 3 | Payment routing | Direct to provider: Maydon sends payment request to Paynet, Paynet pays provider directly (same integration as Tenant flow) |
| 4 | Multi-select | Owner can select and pay multiple bills at once across different properties |
| 5 | Payment visibility | Both Tenant and Owner can see the payment receipt; Tenant sees "Paid by Owner" |
| 6 | Card saving | Owner can save card (corporate or personal) after entering details — available for both one-time and auto-pay |
| 7 | Payment method | Paynet (sole payment method), direct payment to provider via Paynet |
| 8 | Auto-payment | Included in v1 — scheduled recurring payments for Owner-responsible accounts |
| 9 | Debt context | When Owner takes responsibility for an account with pre-existing debt, the UI transparently shows the breakdown |

---

## 1. High-Level Owner Payment Flow Overview

```mermaid
flowchart TD
    START["Owner opens<br/>'Utilities' section"] --> DASHBOARD["Utilities Dashboard<br/>(aggregate view across<br/>all properties)"]

    DASHBOARD --> PAYABLE["My Payable Bills<br/>(accounts where<br/>responsibility = Owner)"]

    PAYABLE --> SELECT_BILLS["Select bills to pay<br/>(multi-select supported)"]

    SELECT_BILLS --> TOTAL["Review total<br/>amount"]

    TOTAL --> CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)<br/>or Select Saved Card"]

    CARD_DETAILS --> PAY_OPTS{"Payment Option"}

    PAY_OPTS -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    PAY_OPTS -->|"Auto-pay"| SCHEDULE["Set Auto-Pay Schedule<br/>(day of month + amount)"]
    SCHEDULE --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["Owner enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM["Confirm Payment<br/>(amount, provider, account)"]
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM --> RECEIPT["Payment Receipt<br/>(visible to Owner + Tenant)"]
    RECEIPT --> UPDATE_STATUS["Update Tenant View:<br/>'Paid by Owner'"]
    RECEIPT --> NOTIFY_TENANT["Push notification<br/>sent to Tenant"]
```

---

## 2. Detailed User Flow — Step-by-Step

### Step 1: Open "Utilities" Section → Dashboard → Payment Queue

```mermaid
flowchart LR
    OPEN["Owner opens<br/>'Utilities' section"] --> DASH["Utilities Dashboard<br/>(landing page)"]
    DASH --> QUEUE["Owner's Payment Queue:<br/>My Payable Bills (3)"]
    QUEUE --> LIST["Show payable bills:<br/>• Provider name<br/>• Account number<br/>• Amount due<br/>• Property address<br/>• Due date"]
    LIST --> SELECT["Owner selects<br/>bills to pay"]
    SELECT --> NEXT["→ Step 2"]
```

**Screen:** Utilities Dashboard with a prominent "My Payable Bills" section at the top. Shows a count badge (e.g., "3") indicating the number of outstanding owner-responsible bills.  
**Data source:** Fetches all utility accounts for the owner's properties where `responsibility_type = 'owner'` and there is an outstanding balance. Also includes any tenant bills the owner has chosen to pay voluntarily.  
**Display:** Each bill card shows: Provider icon + name, лицевой счет number, amount due, property address, due date, and a checkbox for multi-select.

---

### Step 2: Select Bills & Review Total

```mermaid
flowchart TD
    BILLS["Owner's Payable Bills:<br/>━━━━━━━━━━━━━━━━━━<br/>☑ Electricity (Apt 12, Bldg A)<br/>  Account: #1234567890<br/>  Amount: 50,000 UZS<br/>  Due: Feb 15<br/>━━━━━━━━━━━━━━━━━━<br/>☑ HOA (Apt 12, Bldg A)<br/>  Account: #888999<br/>  Amount: 150,000 UZS<br/>  Due: Feb 10<br/>━━━━━━━━━━━━━━━━━━<br/>☐ Gas (Apt 5, Bldg B)<br/>  Account: #5554443322<br/>  Amount: 20,000 UZS<br/>  Due: Feb 20"] --> ACTIONS{"Selection"}

    ACTIONS -->|"Select All"| ALL["All bills selected"]
    ACTIONS -->|"Select specific"| SOME["Partial selection"]

    ALL --> TOTAL["Total: 220,000 UZS<br/>(3 bills)"]
    SOME --> TOTAL_PARTIAL["Total: 200,000 UZS<br/>(2 bills selected)"]

    TOTAL --> NEXT["→ Step 3: Payment"]
    TOTAL_PARTIAL --> NEXT
```

**Key UX considerations:**
- **Multi-select support.** Owner can check/uncheck individual bills or use "Select All"
- **Per-property grouping.** Bills are grouped by property for clarity (e.g., "Apt 12, Building A" has two bills underneath)
- **Sort/filter options.** Owner can sort by: Due date (nearest first), Amount (highest first), Property
- **Debt context banner.** If any account has pre-existing debt from before the owner took responsibility, a subtle warning appears:

> ⚠️ **Total Due: 150,000 UZS** — Includes approx. 100,000 UZS incurred before you took responsibility.

---

### Step 3: Payment

```mermaid
flowchart TD
    ACC["Bills selected:<br/>2 bills, Total: 200,000 UZS<br/>━━━━━━━━━━━━━━━<br/>Electricity #12345: 50,000 UZS<br/>HOA #888999: 150,000 UZS"] --> EDIT_AMT{"Edit Amount?"}
    EDIT_AMT -->|"Pay full balance"| CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)<br/>or Select Saved Card<br/>(Corporate / Personal)"]
    EDIT_AMT -->|"Custom amount<br/>(per bill)"| CUSTOM_AMT["Enter custom amount<br/>for each selected bill"] --> CARD_DETAILS

    CARD_DETAILS --> PAY_OPTS{"Payment Option"}

    PAY_OPTS -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    PAY_OPTS -->|"Auto-pay"| SCHED["Configure auto-pay:<br/>• Day of month (1-28)<br/>• Fixed amount or 'Full balance'<br/>• Start date<br/>• Per-account config"]
    SCHED --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["Owner enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM["Confirm Payment<br/>━━━━━━━━━━━━━━━<br/>Provider: ЭЛЕКТРИЧЕСТВО<br/>Account: #12345<br/>Amount: 50,000 UZS<br/>━━━━━━━━━━━━━━━<br/>Provider: HOA (ТЧСЖ)<br/>Account: #888999<br/>Amount: 150,000 UZS<br/>━━━━━━━━━━━━━━━<br/>Method: Paynet<br/>Service fee: 1,000 UZS<br/>━━━━━━━━━━━━━━━<br/>Total: 201,000 UZS"]

    CONFIRM --> DONE["Payment Complete"]
    DONE --> RECEIPT["Receipt generated:<br/>PDF download +<br/>Push notification to Owner"]
    RECEIPT --> NOTIFY_TENANT["Push notification<br/>sent to Tenant:<br/>'Owner paid ЭЛЕКТРИЧЕСТВО<br/>50,000 UZS + HOA 150,000 UZS'"]
    RECEIPT --> UPDATE["Update Tenant View:<br/>'Paid by Owner'"]
```

**Key UX considerations:**
- **Saved cards.** Owner can select from previously saved cards (labeled Corporate or Personal) or enter a new card
- **Custom amounts.** When choosing custom amounts, the owner sets the amount per-bill (not a single total). Each bill can be partially paid
- **Multi-bill payment.** Paynet processes each bill payment individually, but the UX presents it as a single checkout for convenience
- **Service fee.** Displayed clearly before confirmation — per-transaction fee from Paynet
- **Receipt.** Shows the Owner's name as payer. Both Owner and Tenant can view the receipt

---

### Step 4: Auto-Pay Management (Owner)

```mermaid
flowchart TD
    MANAGE["Owner opens<br/>'Auto-Pay' settings"] --> LIST["Owner's Active Auto-Pays:<br/>━━━━━━━━━━━━━━━━━━<br/>HOA #888999 (Apt 12, Bldg A)<br/>  Day: 1st, Amount: Full balance<br/>  Next: March 1, 2026<br/>  Card: •••• 4242 (Corporate)<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity #12345 (Apt 12, Bldg A)<br/>  Day: 5th, Amount: Full balance<br/>  Next: March 5, 2026<br/>  Card: •••• 4242 (Corporate)<br/>━━━━━━━━━━━━━━━━━━<br/>Gas #5554443322 (Apt 5, Bldg B)<br/>  No auto-pay configured"]

    LIST --> ADD["+ Add Auto-Pay<br/>(for accounts without it)"]
    LIST --> EDIT["Edit schedule"]
    LIST --> PAUSE["Pause auto-pay"]
    LIST --> DELETE["Cancel auto-pay"]

    ADD --> CONFIG["Configure Auto-Pay:<br/>━━━━━━━━━━━━━━━━━━<br/>Account: Gas #5554443322<br/>Day of month: [___]<br/>Amount: Full balance / Fixed<br/>Card: [Select saved card]"]
    CONFIG --> SAVE_AP["Save & Activate"]

    EDIT --> SAVE["Save changes"]
    PAUSE --> PAUSED["Auto-pay paused<br/>(resumes on tap)"]
    DELETE --> CONFIRM["Confirm cancellation"]
```

**How it works:**
- **Only for Owner-responsible accounts.** Auto-pay can only be configured for accounts where `responsibility = Owner`
- **Card selection.** Owner selects from saved cards or adds a new one. Cards can be labeled (e.g., "Corporate AmEx," "Personal Visa")
- **Schedule.** Configurable per account — each account can have its own schedule (day of month, amount type)
- **Notifications.** Owner receives a push notification before each auto-pay execution (1 day before) and after (success/failure)

---

### Step 5: Voluntary Tenant Bill Payment

> **Context:** Sometimes the Owner wants to pay a tenant's overdue bill as a gesture or to avoid provider penalties, even though responsibility is set to "Tenant."

```mermaid
flowchart TD
    DASH["Owner views<br/>Payment History"] --> OVERDUE["Sees overdue tenant bills:<br/>━━━━━━━━━━━━━━━━━━<br/>⚠️ Water (Apt 12): 45,000 UZS<br/>  Overdue by: 15 days<br/>  Responsibility: Tenant<br/>  Status: Unpaid"]

    OVERDUE --> PAY_BTN["'Pay on behalf<br/>of Tenant' button"]

    PAY_BTN --> CONFIRM_INTENT["Confirmation dialog:<br/>━━━━━━━━━━━━━━━━━━<br/>You are paying this bill<br/>on behalf of Тошматов Жасур.<br/>This does NOT change the<br/>responsibility setting.<br/>━━━━━━━━━━━━━━━━━━<br/>[Confirm] [Cancel]"]

    CONFIRM_INTENT -->|"Confirm"| PAYMENT_FLOW["→ Standard Payment Flow<br/>(Card → OTP → Confirm)"]
    CONFIRM_INTENT -->|"Cancel"| BACK["Return to dashboard"]

    PAYMENT_FLOW --> SUCCESS["Payment Complete"]
    SUCCESS --> RECEIPT["Receipt:<br/>Payer: Owner (Voluntary)<br/>Original Responsibility: Tenant"]
    SUCCESS --> NOTIFY_T["Push to Tenant:<br/>'Your Water bill (45,000 UZS)<br/>was paid by your landlord'"]
```

**Key UX considerations:**
- **No responsibility change.** Paying on behalf does NOT flip the responsibility toggle. The tenant will still be responsible for future bills on this account
- **Receipt labeling.** The receipt clearly shows "Payer: Owner (Voluntary)" to distinguish from bills where the owner is the assigned payer
- **Tenant notification.** Tenant receives a push notification acknowledging the payment

---

## 3. Payment Queue Sources

```mermaid
flowchart TD
    START["Owner's Payment<br/>Queue populated by"] --> SOURCE_A["Source 1: Responsibility = Owner<br/>(automatic)<br/>━━━━━━━━━━━━━━━━━━<br/>Bills generated for accounts<br/>where Owner is the assigned payer"]

    START --> SOURCE_B["Source 2: Metered Billing<br/>(automatic)<br/>━━━━━━━━━━━━━━━━━━<br/>Owner submits meter reading →<br/>System calculates cost →<br/>If responsibility = Owner,<br/>bill goes to Owner Queue"]

    START --> SOURCE_C["Source 3: Voluntary Payment<br/>(manual)<br/>━━━━━━━━━━━━━━━━━━<br/>Owner chooses to pay a<br/>tenant's overdue bill"]

    SOURCE_A --> QUEUE["Owner's<br/>Payment Queue"]
    SOURCE_B --> QUEUE
    SOURCE_C --> QUEUE

    QUEUE --> PAY["Owner Payment<br/>(Paynet Checkout)"]
```

---

## 4. Owner Payment vs Tenant Payment Comparison

| Aspect | Tenant Flow | Owner Flow |
|--------|------------|------------|
| **Entry point** | "Pay" section → "Utilities" | "Utilities" Dashboard → "My Payable Bills" |
| **Property selection** | Selects from active leases | Selects from owned properties (or pays from queue) |
| **Bill source** | Bills where `responsibility = Tenant` | Bills where `responsibility = Owner` + voluntary payments |
| **Multi-select** | No (pays one bill at a time) | Yes (can pay multiple bills at once) |
| **Provider selection** | Yes (flat list) | No (bills already linked to specific providers) |
| **Лицевой счет** | Pre-filled (read-only) or manual entry | Already configured by Owner in Account Management |
| **Amount editing** | Pay full balance or custom | Pay full balance or custom (per bill) |
| **Card types** | Personal cards | Corporate or Personal cards |
| **Auto-pay** | Per account, tenant-controlled | Per account, owner-controlled (only for owner-responsible accounts) |
| **Payment method** | Paynet | Paynet (same integration) |
| **OTP verification** | Yes | Yes |
| **Receipt** | "Paid by: Tenant" | "Paid by: Owner" or "Paid by: Owner (Voluntary)" |
| **Notification** | Push to Owner | Push to Tenant |
| **Debt context** | Not applicable | Shows pre-existing debt breakdown when responsibility was transferred |

---

## 5. Auto-Pay for Owner: Execution Flow

```mermaid
flowchart TD
    CRON["Scheduled Job<br/>(daily at 06:00 UTC+5)"] --> CHECK["Check for owner auto-pays<br/>due today"]

    CHECK --> FOUND{"Auto-pay<br/>due today?"}

    FOUND -->|"No"| SKIP["Skip — no action"]
    FOUND -->|"Yes"| FETCH["Fetch current balance<br/>from Paynet"]

    FETCH --> CALC{"Amount type?"}

    CALC -->|"Full balance"| USE_BALANCE["Amount = Paynet balance"]
    CALC -->|"Fixed"| USE_FIXED["Amount = configured<br/>fixed amount"]

    USE_BALANCE --> PROCESS["Process payment via<br/>saved card token"]
    USE_FIXED --> PROCESS

    PROCESS --> RESULT{"Payment<br/>result?"}

    RESULT -->|"Success"| SUCCESS["Mark as paid<br/>+ Generate receipt"]
    SUCCESS --> NOTIFY_S["Push to Owner:<br/>'Auto-pay successful:<br/>HOA #888999 — 150,000 UZS'"]
    SUCCESS --> TENANT_S["Update Tenant View:<br/>'Paid by Owner (Auto-pay)'"]

    RESULT -->|"Failed"| FAIL["Payment failed"]
    FAIL --> RETRY["Retry in 4 hours<br/>(max 3 attempts)"]
    FAIL --> NOTIFY_F["Push to Owner:<br/>'Auto-pay failed:<br/>HOA #888999 — Check your card'"]

    RETRY --> RETRY_CHECK{"Retry count?"}
    RETRY_CHECK -->|"< 3"| PROCESS
    RETRY_CHECK -->|"= 3"| GIVE_UP["Mark as failed<br/>Requires manual payment"]
    GIVE_UP --> URGENT_NOTIFY["Urgent Push:<br/>'Auto-pay failed 3 times<br/>for HOA #888999.<br/>Please pay manually.'"]
```

---

## 6. Integration Points Summary

```mermaid
flowchart LR
    subgraph "Maydon Platform"
        MOBILE["Mobile App<br/>(React Native)"]
        API["maydon-api"]
    end

    subgraph "Paynet"
        PAYNET["Paynet<br/>Aggregator API"]
    end

    subgraph "Utility Providers (390+)"
        ELEC["Electricity"]
        GAS["Gas"]
        WATER["Water"]
        HEAT["Heating"]
        WASTE["Waste"]
    end

    MOBILE -->|"1. Owner initiates payment"| API
    API -->|"2. Pay Directly"| PAYNET

    PAYNET --> ELEC
    PAYNET --> GAS
    PAYNET --> WATER
    PAYNET --> HEAT
    PAYNET --> WASTE
```


