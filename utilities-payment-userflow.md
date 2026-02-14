# Utilities Payment — Tenant User Flow & API Design

> **Module:** `utility` (new module)  
> **Actor:** Tenant (Client role, `typ: "Client"` in JWT)  
> **Integration:** Paynet (utility aggregator, 390+ providers)  
> **Payment Method:** Paynet → Direct payment to provider via Paynet Aggregator  

---

## Design Decisions (Confirmed)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Scope | All utility types displayed as a flat list (Electricity, Gas, Water, Heating, Waste, HOA, Intercom, etc.) — no category grouping |
| 2 | Metering relationship | Hybrid: metered → readings + billing engine; non-metered → Paynet direct via лицевой счет |
| 3 | Лицевой счет ownership | Owner pre-fills (read-only for Tenant); if not pre-filled, Tenant can add |
| 4 | Payment routing | Direct to provider: Maydon sends payment request to Paynet, Paynet pays provider directly |
| 5 | Payment visibility | Both Tenant and Landlord can see utility payment history |
| 6 | Account persistence | Tenant saves лицевой счет numbers, re-pays quickly each month |
| 7 | Payment method | Paynet (sole payment method), direct payment to provider via Paynet |
| 8 | Auto-payment | Included in v1 — scheduled recurring utility payments |
| 9 | Card saving | Tenant can save card after entering details — available for both one-time and auto-pay |

---

## 1. High-Level User Flow Overview

```mermaid
flowchart TD
    START["Tenant opens<br/>'Pay' section"] --> PAY_MENU["Choose payment type:<br/>Rent / Utilities / Services"]

    PAY_MENU --> UTILITIES["Tenant taps 'Utilities'"]

    UTILITIES --> SELECT_PROP["Select Rented Property<br/>(from active leases)"]

    SELECT_PROP --> UTIL_TYPE["Select Provider<br/>(flat list: Electricity, Gas,<br/>Water, Heating, Waste, HOA,<br/>Intercom, Security, ...)"]

    UTIL_TYPE --> PROVIDER["Enter Лицевой Счет"]

    PROVIDER --> CHECK_PREFILL{"Owner pre-filled<br/>лицевой счет?"}

    CHECK_PREFILL -->|"Yes"| PREFILLED["Show лицевой счет<br/>(pre-filled by Owner,<br/>read-only for Tenant)"]
    CHECK_PREFILL -->|"No"| EMPTY_INPUT["Show empty field:<br/>Tenant enters лицевой счет"]

    PREFILLED --> AMOUNT["Fetch balance / debt<br/>from Paynet"]
    EMPTY_INPUT --> VALIDATE["Validate account<br/>via Paynet"]
    VALIDATE -->|"Valid"| AMOUNT
    VALIDATE -->|"Invalid"| ERROR["Show error<br/>'Account not found'"]
    ERROR --> EMPTY_INPUT

    AMOUNT --> EDIT_AMT{"Edit Amount?"}
    EDIT_AMT -->|"Pay full balance"| CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)"]
    EDIT_AMT -->|"Custom amount"| CUSTOM_AMT["Enter custom amount"] --> CARD_DETAILS

    CARD_DETAILS --> PAY_OPTS{"Payment Option"}

    PAY_OPTS -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    PAY_OPTS -->|"Auto-pay"| SCHEDULE["Set Auto-Pay Schedule<br/>(day of month + amount)"]
    SCHEDULE --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["User enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM["Confirm Payment<br/>(amount, provider, account)"]
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM --> RECEIPT["Payment Receipt<br/>(visible to Tenant + Landlord)"]
    RECEIPT --> NOTIFY_OWNER["Push notification<br/>sent to Owner"]

```

---

## 2. Detailed User Flow — Step-by-Step

### Step 1: Open "Pay" Section → Choose "Utilities" → Select Property

```mermaid
flowchart LR
    OPEN["Tenant opens<br/>'Pay' section"] --> MENU["Choose:<br/>Rent / Utilities / Services"]
    MENU --> PICK_UTIL["Tenant taps<br/>'Utilities'"]
    PICK_UTIL --> API_LEASES["Fetch tenant's<br/>active properties"]
    API_LEASES --> LIST["Show property cards:<br/>• Address<br/>• Building name<br/>• Apartment #<br/>• Owner company"]
    LIST --> SELECT["Tenant taps<br/>a property"]
    SELECT --> NEXT["→ Step 2"]

```

**Screen:** "Pay" section with three large tiles: Rent, Utilities, Services. After tapping "Utilities" — property selector carousel/list.  
**Data source:** Uses the tenant's active lease data to show all properties they're currently renting.  
**Display:** Property photo (from real estate images), address, building name, owner company name.

---

### Step 2: Select Provider

```mermaid
flowchart TD
    PROP["Property selected:<br/>'Apartment 42, Building A-1'"] --> UTIL_TYPE["Select Provider"]

    UTIL_TYPE --> UT_LIST["Tabiiy Gaz<br/>Elektroenergiya<br/>Elektroenergiya Yur<br/>Suyultirilgan Gaz<br/>Sovuq suv<br/>Chiqindilarni olib ketish<br/>Tabiiy Gaz Yur<br/>Issiq suv va issiqlik ta'minoti<br/>Mening uyim (XUJMSH)<br/>Ichimlik Suvi Yur<br/>Issiqlik ta'minoti<br/>Issiq suv va issiqlik ta'minoti Yur"]

    UT_LIST --> PROVIDER["Enter Лицевой Счет"]

```

**Screen:** Scrollable grid of utility types, each with icon + name. Search bar at top for filtering.  
**Data source:** Fetches the list of available utility providers, filterable by utility type (e.g. Gas, Electricity, Water).

---

### Step 3: Enter Лицевой Счет

```mermaid
flowchart TD
    PROV["Tenant selects<br/>'ЭЛЕКТРИЧЕСТВО'"] --> CHECK{"Owner pre-filled<br/>лицевой счет?"}

    CHECK -->|"Yes"| PREFILLED["Field pre-filled (read-only):<br/>━━━━━━━━━━━━━━━━━━━━<br/>Лицевой счет: 1234567890<br/>(pre-filled by Owner)<br/>━━━━━━━━━━━━━━━━━━━━<br/>Tenant cannot edit"]

    CHECK -->|"No"| EMPTY["Empty input field:<br/>━━━━━━━━━━━━━━━━━━━━<br/>Лицевой счет: [__________]<br/>Enter your account number"]

    PREFILLED --> FOUND["Account info (already validated):<br/>━━━━━━━━━━━━━━━━━━━━<br/>Provider: ЭЛЕКТРИЧЕСТВО<br/>Owner: Toshmatov J.<br/>Address: Chilanzar 12<br/>Balance: 50,000 UZS"]

    EMPTY --> VALIDATE["Validate account<br/>via Paynet"]
    VALIDATE -->|"Valid"| FOUND
    VALIDATE -->|"Invalid"| NOTFOUND["Account not found.<br/>Check number and try again."]
    NOTFOUND --> EMPTY

    FOUND --> NEXT["→ Step 4: Payment"]
```

**Key UX considerations:**

- **No saved accounts list.** The tenant sees a single лицевой счет input field — either pre-filled or empty
- If the **Owner pre-filled** the лицевой счет (via the Owner's "Manage Utility Accounts" flow), it appears in the field automatically. **The field is read-only (locked) — the tenant cannot edit it.** This prevents tenants from accidentally or intentionally changing a verified account number set by the property owner
- **No re-validation needed for pre-filled accounts.** The owner already validated the account via Paynet when adding it (see Owner flow, Step 5). The tenant skips validation and goes straight to viewing the balance/debt
- If the Owner **did not pre-fill**, the field is empty and the tenant types the лицевой счет number manually — this requires Paynet validation before proceeding
- Balance/debt is fetched from Paynet after the account is confirmed (either pre-validated by Owner or validated by Tenant)
- For **metered utilities** (electricity, gas, water): if the property has meters in our system, show the meter readings data alongside the Paynet balance for cross-reference

---

### Step 4: Payment

```mermaid
flowchart TD
    ACC["Account selected:<br/>'ЭЛЕКТРИЧЕСТВО #12345'<br/>Balance: 50,000 UZS"] --> EDIT_AMT{"Edit Amount?"}
    EDIT_AMT -->|"Pay full balance"| CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)"]
    EDIT_AMT -->|"Custom amount"| CUSTOM_AMT["Enter custom amount"] --> CARD_DETAILS

    CARD_DETAILS --> PAY_OPTS{"Payment Option"}

    PAY_OPTS -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    PAY_OPTS -->|"Auto-pay"| SCHED["Configure auto-pay:<br/>• Day of month (1-28)<br/>• Fixed amount or 'Full balance'<br/>• Start date"]
    SCHED --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["User enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM["Confirm Payment<br/>━━━━━━━━━━━━━━━<br/>Provider: ЭЛЕКТРИЧЕСТВО<br/>Account: #12345<br/>Amount: 50,000 UZS<br/>Method: Paynet<br/>Service fee: 500 UZS<br/>━━━━━━━━━━━━━━━<br/>Total: 50,500 UZS"]

    CONFIRM --> DONE["Payment Complete"]
    DONE --> RECEIPT["Receipt generated:<br/>PDF download +<br/>Push notification to Tenant"]
    RECEIPT --> NOTIFY_OWNER["Push notification<br/>sent to Owner:<br/>'Tenant paid ЭЛЕКТРИЧЕСТВО<br/>50,000 UZS'"]

```

---

### Step 5: Auto-Pay Management

```mermaid
flowchart TD
    MANAGE["Tenant opens<br/>'Auto-Pay' settings"] --> LIST["Active auto-pays:<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity #12345<br/>  Day: 1st, Amount: Full balance<br/>  Next: March 1, 2026<br/>  Method: Paynet"]

    LIST --> EDIT["Edit schedule"]
    LIST --> PAUSE["Pause auto-pay"]
    LIST --> DELETE["Cancel auto-pay"]

    EDIT --> SAVE["Save changes"]
    PAUSE --> PAUSED["Auto-pay paused<br/>(resumes on tap)"]
    DELETE --> CONFIRM["Confirm cancellation"]

```

---


## 3. Metered vs Non-Metered Settlement Flow

```mermaid
flowchart TD
    START["Utility billing<br/>triggered"] --> CHECK{"Meter<br/>installed?"}

    CHECK -->|"Yes (Metered)"| M_READ["Owner submits<br/>meter reading"]
    CHECK -->|"No (Non-Metered)"| NM_CAT["System determines<br/>calculation category<br/>based on service type"]

    M_READ --> M_CALC["Billing engine calculates<br/>consumption × tariff = cost"]
    NM_CAT --> NM_CALC["Billing engine calculates<br/>tariff × variable<br/>(Residents / Area / Volume)"]

    M_CALC --> CHARGE["Utility charge created<br/>(amount known)"]
    NM_CALC --> CHARGE

    CHARGE --> EDIT_AMT{"Edit Amount?"}
    EDIT_AMT -->|"Pay full balance"| CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)"]
    EDIT_AMT -->|"Custom amount"| CUSTOM_AMT["Enter custom amount"] --> CARD_DETAILS

    CARD_DETAILS --> PAY_OPTS{"Payment Option"}

    PAY_OPTS -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    PAY_OPTS -->|"Auto-pay"| SCHEDULE["Set Auto-Pay Schedule<br/>(day of month + amount)"]
    SCHEDULE --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["User enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM["Confirm Payment<br/>(amount, provider, account)"]
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM --> RECEIPT["Payment Receipt<br/>(visible to Tenant + Landlord)"]
    RECEIPT --> NOTIFY["Push notification<br/>sent to Owner"]
```

---

## 4. Owner Pre-Fill Flow (Landlord Side)

```mermaid
flowchart LR
    OWNER["Owner / Agent<br/>adds property"] --> SECTION["Opens 'Utility Accounts'<br/>section for the property"]

    SECTION --> ADD["Taps '+ Add<br/>utility account'"]
    ADD --> FILL["Provider: ЭЛЕКТРИЧЕСТВО<br/>Лицевой счет: 12345<br/>Label: 'Main electricity'"]
    FILL --> VALIDATE["Validate via Paynet"]
    VALIDATE --> SAVE["Save to<br/>utility_accounts<br/>(source='owner')"]

    SAVE --> TENANT_VIEW["When Tenant opens<br/>'Utilities' → sees<br/>pre-filled accounts"]

```

---

## 5. Landlord View — Utility Payment History

```mermaid
flowchart TD
    OWNER["Landlord opens<br/>'Tenant Utilities'"] --> SELECT["Select property<br/>& tenant"]
    SELECT --> HISTORY["Utility Payment History<br/>━━━━━━━━━━━━━━━━━━━━<br/>Feb 2026<br/>Electricity — 50,000 UZS — Paid Feb 1<br/>Water — 25,000 UZS — Paid Feb 3<br/>Gas — Pending<br/>HOA — 150,000 UZS — Paid Feb 5<br/>━━━━━━━━━━━━━━━━━━━━<br/>Jan 2026<br/>Electricity — 48,000 UZS — Paid Jan 2<br/>Water — 22,000 UZS — Paid Jan 4<br/>..."]

    HISTORY --> DETAIL["Tap payment →<br/>Receipt detail:<br/>Paynet transaction ID,<br/>Payment method,<br/>Date and time,<br/>Provider confirmation"]

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
        HOA["HOA / ТЧСЖ"]
        ANCIL["Intercom,<br/>Security, etc."]
    end

    MOBILE -->|"1. Pay"| API
    API -->|"2. Pay Directly"| PAYNET

    PAYNET --> ELEC
    PAYNET --> GAS
    PAYNET --> WATER
    PAYNET --> HEAT
    PAYNET --> WASTE
    PAYNET --> HOA
    PAYNET --> ANCIL

```
