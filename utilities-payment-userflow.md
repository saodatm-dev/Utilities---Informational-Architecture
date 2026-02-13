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
| 3 | Лицевой счет ownership | Both: Owner pre-fills, Tenant can add/edit |
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

    SELECT_PROP --> UTIL_TYPE["Choose Utility Type<br/>(flat list: Electricity, Gas,<br/>Water, Heating, Waste, HOA,<br/>Intercom, Security, ...)"]

    UTIL_TYPE --> PROVIDER["Select Utility Provider"]

    PROVIDER --> FETCH_ACCOUNTS["System: Fetch saved<br/>лицевых счетов<br/>(GET /api/v1/utility/accounts)"]

    FETCH_ACCOUNTS --> LIST_SCREEN["Show list of saved<br/>лицевых счетов<br/>(with balances + 'Add' button)"]

    LIST_SCREEN --> SELECT_SAVED["User selects<br/>saved account"]
    LIST_SCREEN --> ADD["User taps<br/>'+ Add лицевой счет'"]

    ADD --> VALIDATE["Validate account<br/>via Paynet"]
    VALIDATE -->|"Valid"| SAVE["Save account<br/>(name + number)"]
    VALIDATE -->|"Invalid"| ERROR["Show error<br/>'Account not found'"]
    ERROR --> ADD

    SAVE --> LIST_SCREEN
    SELECT_SAVED --> AMOUNT["Fetch balance / debt<br/>from Paynet"]

    AMOUNT --> EDIT_CHECK{"Edit amount?"}
    EDIT_CHECK -->|"No, pay exact amount"| PAY_OPTS
    EDIT_CHECK -->|"Yes"| EDIT_AMOUNT["User enters<br/>custom amount"]
    EDIT_AMOUNT --> PAY_OPTS

    PAY_OPTS{"Payment Option"}
    PAY_OPTS -->|"One-time"| CARD_DETAILS
    PAY_OPTS -->|"Auto-pay"| CARD_DETAILS_AUTO["Enter Credit/Card Details<br/>(card number, expiry date)"]

    CARD_DETAILS_AUTO --> SCHEDULE["Set Auto-Pay Schedule<br/>(day of month + amount)"]
    CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)"]

    CARD_DETAILS --> SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    SCHEDULE --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"]
    AUTO_SAVE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["User enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM["Confirm Payment<br/>(amount, provider, account)"]
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM --> PAYNET["Pay Provider Directly<br/>via Paynet"]

    PAYNET --> RECEIPT["Payment Receipt<br/>(visible to Tenant + Landlord)"]
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

### Step 2: Choose Utility Type

```mermaid
flowchart TD
    PROP["Property selected:<br/>'Apartment 42, Building A-1'"] --> UTIL_TYPE["Choose Utility Type"]

    UTIL_TYPE --> UT_LIST["Tabiiy Gaz<br/>Elektroenergiya<br/>Elektroenergiya Yur<br/>Suyultirilgan Gaz<br/>Sovuq suv<br/>Chiqindilarni olib ketish<br/>Tabiiy Gaz Yur<br/>Issiq suv va issiqlik ta'minoti<br/>Mening uyim (XUJMSH)<br/>Ichimlik Suvi Yur<br/>Issiqlik ta'minoti<br/>Issiq suv va issiqlik ta'minoti Yur"]

    UT_LIST --> PROVIDER["Select Provider<br/>(within chosen type)"]

```

**Screen:** Scrollable grid of utility types, each with icon + name. Search bar at top for filtering.  
**Data source:** Fetches the list of available utility providers, filterable by utility type (e.g. Gas, Electricity, Water).

---

### Step 3: Select Provider → Show List of Saved Лицевых Счетов → Add / Select

```mermaid
flowchart TD
    PROV["Tenant selects<br/>'ЭЛЕКТРИЧЕСТВО'"] --> FETCH["System: Fetch saved accounts"]

    FETCH --> LIST_SCREEN["System shows:<br/>List of saved лицевых счетов<br/>━━━━━━━━━━━━━━━━━━━━<br/>Account #12345<br/>  Balance: 50,000 UZS owed<br/>Account #67890<br/>  Balance: 0 (paid up)<br/>━━━━━━━━━━━━━━━━━━━━<br/>[ + Add лицевой счет ]"]

    LIST_SCREEN --> SELECT_ACC["User selects<br/>saved account to pay"]
    LIST_SCREEN --> ADD_FLOW["User taps<br/>'+ Add лицевой счет'"]

    SELECT_ACC --> NEXT["→ Step 4: Payment"]

    ADD_FLOW --> INPUT["Enter лицевой счет<br/>абонемента (number)"]
    INPUT --> LABEL["Enter account label<br/>(optional, e.g. 'Main meter')"]
    LABEL --> VALIDATE["Validate account<br/>via Paynet"]

    VALIDATE -->|"Valid"| FOUND["Account found:<br/>'ЭЛЕКТРИЧЕСТВО'<br/>Owner: Toshmatov J.<br/>Address: Chilanzar 12<br/>Balance: 50,000 UZS"]
    VALIDATE -->|"Invalid"| NOTFOUND["Account not found.<br/>Check number and try again."]
    NOTFOUND --> INPUT

    FOUND --> SAVE_BTN["Tenant taps 'Save Account'"]
    SAVE_BTN --> SAVED["Account saved<br/>successfully"]
    SAVED --> LIST_SCREEN

```

**Key UX considerations:**
- **System always shows the saved accounts list** — after the user selects a provider, the system fetches and displays all saved лицевых счетов for that provider/lease combination. This is a system-initiated action, not a user action.
- The list screen **always includes a "+ Add лицевой счет" button** at the bottom, so the user can add a new account at any time.
- If no saved accounts exist (first time), the list appears empty with an empty-state message and the "+ Add лицевой счет" button.
- Owner-prefilled accounts should appear automatically (marked as "Owner" source).
- Tenant-added accounts marked as "Tenant" source.
- Balance/debt displayed in real-time from Paynet (fetched with `include_balance=true`).
- After saving a new account, the user is returned to the list screen (now including the newly added account).
- For **metered utilities** (electricity, gas, water): if the property has meters in our system, show the meter readings data alongside the Paynet balance for cross-reference.

---

### Step 4: Payment

```mermaid
flowchart TD
    ACC["Account selected:<br/>'ЭЛЕКТРИЧЕСТВО #12345'<br/>Balance: 50,000 UZS"] --> TYPE{"Payment Type"}

    TYPE -->|"One-time"| AMOUNT["Enter amount or<br/>pay full balance"]
    TYPE -->|"Auto-pay"| SCHED["Configure auto-pay:<br/>• Day of month (1-28)<br/>• Fixed amount or 'Full balance'<br/>• Start date"]

    AMOUNT --> CARD_DETAILS
    SCHED --> CARD_DETAILS

    CARD_DETAILS["Enter Credit/Card Details<br/>(card number, expiry date)"]

    CARD_DETAILS --> SAVE_CARD{"Save Card?<br/>(for future payments)"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card"]
    SAVE_CARD -->|"No"| SEND_OTP
    TOKENIZE --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["User enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM["Confirm Payment<br/>━━━━━━━━━━━━━━━<br/>Provider: ЭЛЕКТРИЧЕСТВО<br/>Account: #12345<br/>Amount: 50,000 UZS<br/>Method: Paynet<br/>Service fee: 500 UZS<br/>━━━━━━━━━━━━━━━<br/>Total: 50,500 UZS"]

    CONFIRM --> PAY["'Pay Now' button"]
    PAY --> PAYNET_PAY["Paynet pays Provider<br/>directly"]
    PAYNET_PAY --> DONE["Payment Complete"]
    DONE --> RECEIPT["Receipt generated:<br/>PDF download +<br/>Push notification to Tenant"]
    RECEIPT --> NOTIFY_OWNER["Push notification<br/>sent to Owner:<br/>'Tenant paid ЭЛЕКТРИЧЕСТВО<br/>50,000 UZS'"]

```

---

### Step 5: Auto-Pay Management

```mermaid
flowchart TD
    MANAGE["Tenant opens<br/>'Auto-Pay' settings"] --> LIST["Active auto-pays:<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity #12345<br/>  Day: 1st, Amount: Full balance<br/>  Next: March 1, 2026<br/>  Method: Paynet<br/>━━━━━━━━━━━━━━━━━━<br/>Water #67890<br/>  Day: 5th, Amount: Fixed 30,000<br/>  Next: March 5, 2026<br/>  Method: Paynet"]

    LIST --> EDIT["Edit schedule"]
    LIST --> PAUSE["Pause auto-pay"]
    LIST --> DELETE["Cancel auto-pay"]

    EDIT --> SAVE["Save changes"]
    PAUSE --> PAUSED["Auto-pay paused<br/>(resumes on tap)"]
    DELETE --> CONFIRM["Confirm cancellation"]

```

---

## 3. Non-Metered Billing Logic — Calculation Categories

> **Context:** When a property has no meter installed for a given utility, the billing amount is calculated using regulated tariffs and property/tenant variables. Each utility type falls into one of the calculation categories below. All variables must be stored **per-service** (not globally) to avoid cross-contamination between providers.

---

### 3.1 Calculation Categories Overview

```mermaid
flowchart LR
    INPUT["Property Profile<br/>Variables"]

    INPUT --> CAT1
    INPUT --> CAT2
    INPUT --> CAT3
    INPUT --> CAT4

    subgraph CAT1 ["Category 1: Per-Person"]
        direction TB
        C1_FORMULA["Formula:<br/>Tariff × Normatif × Residents"]
        C1_FORMULA --> C1_SERVICES["Cold Water<br/>Hot Water<br/>Gas (cooking/heating water)"]
    end

    subgraph CAT2 ["Category 2: Per-Area"]
        direction TB
        C2_FORMULA["Formula:<br/>Heating: Tariff × Heated Area<br/>HOA: Tariff × Total Area"]
        C2_FORMULA --> C2_SERVICES["Central Heating<br/>HOA / Maintenance fees"]
    end

    subgraph CAT3 ["Category 3: Per-Volume"]
        direction TB
        C3_FORMULA["Formula:<br/>Tariff × Volume (m³)"]
        C3_FORMULA --> C3_SERVICES["Gas Heating<br/>(private house with boiler)"]
    end

    subgraph CAT4 ["Category 4: Fix Per-Person"]
        direction TB
        C4_FORMULA["Formula:<br/>Tariff × Residents"]
        C4_FORMULA --> C4_SERVICES["Waste Collection"]
    end
```

---

### 3.2 Detailed Formulas Per Service

#### Category 1 — Per-Person with Normatif

| Service | Formula | Variables |
|---------|---------|-----------|
| Cold Water (no meter) | `Tariff × Normatif_CW × Residents` | Normatif = liters/person/month |
| Hot Water (no meter) | `Tariff × Normatif_HW × Residents` | Normatif = liters/person/month |
| Gas — cooking | `Tariff × Normatif_Gas × Residents` | Normatif = m³/person/month |

> [!IMPORTANT]
> **Residents count is per-service, not global.** If an inspector from one provider (e.g., Mahsustrans) files an act for 5 actual residents, this does NOT affect the resident count used by another provider (e.g., Suvsoz which still charges for 2 registered). Each utility account must store its own `residents_count` field.

#### Category 2 — Per-Area

| Service | Formula | Area Variable |
|---------|---------|---------------|
| Central Heating | `Tariff × Heated_Area` | `heated_area` — excludes balconies, loggias |
| HOA / Maintenance | `Tariff × Total_Area` | `total_area` — full area including balconies |

> [!WARNING]
> **Two independent area fields required in the property profile:**
> - `total_area` (m²) — used for HOA/maintenance calculations
> - `heated_area` (m²) — used for heating calculations
>
> These values differ for most apartments. Using a single area field will produce incorrect charges for one of the two calculations.

#### Category 3 — Per-Volume (Cubature)

| Service | Formula | Variables |
|---------|---------|-----------|
| Gas Heating (private house, no meter) | `Tariff × Volume` | `volume` = area × ceiling height (m³) |

> [!NOTE]
> This category applies only to private houses with a gas boiler and no gas meter. Volume (m³) depends on ceiling height, which means the property profile must store `ceiling_height` or `volume_m3` directly.

#### Category 4 — Fix Per-Person (no normatif)

| Service | Formula | Variables |
|---------|---------|-----------|
| Waste Collection | `Tariff × Residents` | No normatif — tariff already includes per-person rate |

> [!IMPORTANT]
> Waste collection does NOT use a normatif multiplier. The tariff is already set as a fix rate per person. Applying a normatif would double-count.

---

### 3.3 Sewage (Kanalizatsiya) — Special Logic

Sewage is always calculated as the **sum of cold water and hot water consumption**, regardless of whether those are metered or non-metered:

```
Sewage Volume = Cold_Water_Usage + Hot_Water_Usage
Sewage Amount = Sewage_Tariff × Sewage_Volume
```

| Scenario | Cold Water Source | Hot Water Source | Sewage Calculation |
|----------|-------------------|------------------|--------------------|
| Both metered | Meter reading CW | Meter reading HW | `Sewage = (CW_reading) + (HW_reading)` |
| Both non-metered | `Normatif_CW × Residents` | `Normatif_HW × Residents` | `Sewage = (Norm_CW × Res) + (Norm_HW × Res)` |
| Hybrid (CW metered, HW not) | Meter reading CW | `Normatif_HW × Residents` | `Sewage = (CW_reading) + (Norm_HW × Res)` |

> [!CAUTION]
> The sewage formula must always sum **both** water sources. An algorithm that references a single abstract "water" normatif will break in hybrid scenarios (e.g., cold water meter installed, hot water non-metered).

---

### 3.4 Metered vs Non-Metered Settlement Flow

```mermaid
flowchart TD
    subgraph METERED ["Metered Utilities"]
        M_READ["Owner submits<br/>meter reading<br/>(existing flow)"] --> M_CALC["Billing engine calculates<br/>consumption x tariff = cost"]
        M_CALC --> M_CHARGE["Utility charge created<br/>(amount known)"]
        M_CHARGE --> M_PAY["Tenant sees charge +<br/>Paynet balance side-by-side"]
        M_PAY --> M_CONFIRM["Pay via Paynet<br/>(amount from our system)"]
    end

    subgraph NONMETERED ["Non-Metered Utilities"]
        NM_CAT["System determines<br/>calculation category<br/>(1-4 based on service type)"] --> NM_CALC["Apply formula:<br/>Tariff x Variable<br/>(Residents / Area / Volume)"]
        NM_CALC --> NM_CHARGE["Charge calculated<br/>(amount known)"]
        NM_CHARGE --> NM_PAY["Tenant sees calculated<br/>charge amount"]
        NM_PAY --> NM_CONFIRM["Pay via Paynet<br/>(amount from our system)"]
    end

    M_CONFIRM --> PAYNET["Pay Provider Directly<br/>via Paynet"]
    NM_CONFIRM --> PAYNET

    PAYNET --> RECORD["Receipt Generated<br/>+ PDF download"]
    RECORD --> NOTIFY["Notify Tenant + Landlord"]

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
