# Utilities — Owner (Business) User Flow

> **Module:** `utility` (new module, extends `building` module)  
> **Actor:** Owner / Agent (`typ: "Owner"` or `typ: "Agent"` in JWT)  
> **Existing Backend:** Meter, MeterType, MeterTariff, MeterReading domain models in `Building.Domain`  
> **Integration:** Paynet (utility aggregator)  
> **Related:** [Tenant Utilities Flow](./utilities-payment-userflow.md)

---

## Design Decisions (Confirmed)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Scope | All owner features: meter management, readings, account pre-fill, billing, payment history, auto-pay visibility |
| 2 | Feature tiers | Meters, readings, utility accounts, payment history, dashboard, tariff management, billing engine |
| 3 | Meter readings actor | Owner submits; `submitted_by` field tracks who; system sends overdue reminders |
| 4 | Billing automation | Auto-calculated charges (reading × tariff) go directly to the assigned payer (Tenant or Owner) |
| 5 | Payment visibility | Owner sees all statuses + aggregate dashboard. Owner can pay bills directly if responsibility is theirs |
| 6 | Navigation | Dashboard is landing page → drill down to per-property views |
| 7 | Auto-pay oversight | Owner can see tenant auto-pay status; cannot require tenants to set up auto-pay |
| 8 | Architecture | New utility accounts/billing tables; reuses existing `meters` domain |
| 9 | **Payment Responsibility** | **Per Utility Account.** Explicit toggle: "Tenant pays" (default) or "Owner pays" |

---

## 1. High-Level Owner Flow Overview

```mermaid
flowchart TD
    START["Owner opens<br/>'Utilities' section"] --> DASHBOARD["Utilities Dashboard"]

    DASHBOARD --> ALERTS["Action Items<br/>• Overdue meter readings<br/>• Unpaid utilities"]
    DASHBOARD --> STATS["Summary Stats<br/>• Total collected this month<br/>• Outstanding balance<br/>• Owner payable bills"]
    DASHBOARD --> PROP_LIST["Property List<br/>(all owned real estates<br/>with utility status)"]
    DASHBOARD --> OWNER_BILLS["My Payable Bills<br/>(owner-responsible charges<br/>across all properties)"]

    PROP_LIST --> SELECT_PROP["Select Property"]

    SELECT_PROP --> PROP_VIEW["Property Utility Overview<br/>━━━━━━━━━━━━━━━━━━<br/>Meters | Accounts | Readings<br/>Billing | My Bills | Payments<br/>Auto-Pay Status"]

    PROP_VIEW --> METERS["Manage Meters<br/>(Add / Edit / Link to Account)"]
    PROP_VIEW --> ACCOUNTS["Manage Accounts<br/>(Add / Set Responsibility)"]
    PROP_VIEW --> READINGS["Submit Readings<br/>(monthly meter readings)"]
    PROP_VIEW --> BILLING["Billing<br/>(metered + non-metered charges)"]
    PROP_VIEW --> MY_BILLS["My Bills<br/>(owner-responsible charges)"]
    PROP_VIEW --> PAYMENTS["Payment History<br/>(all payments)"]
    PROP_VIEW --> AUTOPAY["Auto-Pay Status<br/>(tenant configuration)"]

    READINGS --> ROUTE{"Responsibility<br/>Check"}
    ROUTE -->|"Tenant pays"| TENANT_BILL["Bill sent to Tenant"]
    ROUTE -->|"Owner pays"| OWNER_QUEUE["Bill added to<br/>Owner's Payables"]

    OWNER_BILLS --> OWNER_PAY["Owner Payment<br/>(Paynet Checkout)"]
    OWNER_QUEUE --> OWNER_PAY
    MY_BILLS --> OWNER_PAY

    PAYMENTS --> EXPORT["Export PDF Report"]
```

---

## 2. Detailed User Flow — Step-by-Step

### Step 1: Utilities Dashboard

```mermaid
flowchart TD
    OPEN["Owner opens<br/>'Utilities'"] --> LOAD["Load dashboard<br/>summary"]

    LOAD --> DASH["Dashboard View"]

    DASH --> SECTION_A["Action Required<br/>━━━━━━━━━━━━━━━━━━<br/>3 meter readings overdue<br/>2 tenants with unpaid utilities"]

    DASH --> SECTION_B["Monthly Summary<br/>━━━━━━━━━━━━━━━━━━<br/>Total Utility Charges: 2,450,000 UZS<br/>Collected: 1,800,000 UZS<br/>Outstanding: 650,000 UZS<br/>Owner Payable: 220,000 UZS"]

    DASH --> SECTION_C["Properties<br/>━━━━━━━━━━━━━━━━━━<br/>Apt 12, Building A — All paid<br/>Apt 5, Building B — 50,000 UZS due<br/>Apt 8, Building C — Overdue 3 days<br/>Office 3, Building D — All paid<br/>..."]

    DASH --> SECTION_D["My Payable Bills<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya (Apt 12): 50,000 UZS<br/>Issiqlik ta'minoti (Apt 12): 150,000 UZS<br/>Tabiiy Gaz (Apt 5): 20,000 UZS<br/>━━━━━━━━━━━━━━━━━━<br/>Total Due: 220,000 UZS"]

    SECTION_A --> TAP_ACTION["Tap action item<br/>→ navigate to relevant screen"]
    SECTION_C --> TAP_PROP["Tap property<br/>→ Property Utility Overview"]
    SECTION_D --> TAP_BILL["Tap bill<br/>→ Owner Payment Flow (Step 9)"]
```

---

### Step 2: Property Utility Overview (Drill-Down)

```mermaid
flowchart TD
    PROP["Property selected:<br/>'Apartment 12, Building A-1'<br/>Tenant: Тошматов Жасур"] --> TABS["Navigation Tabs"]

    TABS --> T_METERS["Meters<br/>(3 active meters)"]
    TABS --> T_ACCOUNTS["Accounts<br/>(12 лицевой счетов)"]
    TABS --> T_READINGS["Submit Readings<br/>(monthly meter readings)"]
    TABS --> T_BILLING["Billing<br/>(Feb charges)"]
    TABS --> T_MY_BILLS["My Bills<br/>(owner-responsible)"]
    TABS --> T_PAYMENTS["Payments"]
    TABS --> T_AUTOPAY["Auto-Pay<br/>(2 of 12 active)"]

    T_METERS --> METERS_VIEW["Meter List:<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya — SN: E-12345<br/>  Last reading: Feb 1 — 12,450 kWh<br/>Sovuq suv — SN: W-67890<br/>  Last reading: Feb 1 — 234 m³<br/>Tabiiy Gaz — SN: G-11111<br/>  Last reading: Jan 28 — 1,890 m³"]

    T_ACCOUNTS --> ACC_VIEW["Utility Accounts:<br/>━━━━━━━━━━━━━━━━━━<br/>Tabiiy Gaz — #1234567890<br/>Elektroenergiya — #0987654321<br/>Elektroenergiya Yur — #5555666677<br/>Suyultirilgan Gaz — #4443332211<br/>Sovuq suv — #9998887766<br/>Chiqindilarni olib ketish — #1112223344<br/>Tabiiy Gaz Yur — #6667778899<br/>Issiq suv va issiqlik ta'minoti — #3334445566<br/>Mening uyim (XUJMSH) — #888999<br/>Ichimlik Suvi Yur — #2221110099<br/>Issiqlik ta'minoti — #7776665544<br/>Issiq suv va issiqlik ta'minoti Yur — #5554443322"]

    T_BILLING --> BILL_VIEW["Charges for Feb 2026:<br/>━━━━━━━━━━━━━━━━━━<br/>**Metered:**<br/>Elektroenergiya: 112,100 UZS<br/>  380 kWh × 295 UZS/kWh<br/>Sovuq suv: 45,000 UZS<br/>  15 m³ × 3,000 UZS/m³<br/>━━━━━━━━━━━━━━━━━━<br/>**Non-Metered:**<br/>Chiqindilarni olib ketish: 25,000 UZS<br/>  5,000 UZS × 5 residents<br/>Issiqlik ta'minoti: 80,000 UZS<br/>  2,000 UZS × 40 m²<br/>━━━━━━━━━━━━━━━━━━<br/>Total: 262,100 UZS"]

    T_READINGS --> READINGS_VIEW["Submit Reading:<br/>━━━━━━━━━━━━━━━━━━<br/>Select meter → Enter reading<br/>→ Step 4 (detailed flow)"]

    T_MY_BILLS --> MY_BILLS_VIEW["Owner's Payable Bills:<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya: 50,000 UZS — Pending<br/>Issiqlik ta'minoti: 150,000 UZS — Pending<br/>━━━━━━━━━━━━━━━━━━<br/>Total Due: 200,000 UZS"]

    MY_BILLS_VIEW --> PAY_BTN["Pay → Owner Payment Flow<br/>(Step 9)"]
```

---

### Step 3: Manage Meters

```mermaid
flowchart TD
    METERS["Owner opens<br/>'Meters' tab"] --> LIST["Fetch meters<br/>for this property"]

    LIST --> VIEW["Meter List:<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya (Individual)<br/>  Linked Account: #1234567890<br/>  Status: Active<br/>━━━━━━━━━━━━━━━━━━<br/>Sovuq suv<br/>  Linked Account: #9876543210<br/>  Status: Active"]

    VIEW --> ADD_BTN["+ Add Meter"]
    VIEW --> EDIT_BTN["Edit Meter"]

    ADD_BTN --> ADD_FORM["Add Meter Form:<br/>━━━━━━━━━━━━━━━━━━<br/>Meter Type: [dropdown]<br/>Serial Number: [input]<br/>**Лицевой счет: [input]**"]

    ADD_FORM --> VALIDATE_FORM{"Valid?"}
    VALIDATE_FORM -->|"Yes"| SAVE["Save meter<br/>& Link to Account"]
    VALIDATE_FORM -->|"No"| ERROR["Validation errors"]
    ERROR --> ADD_FORM

    SAVE --> SUCCESS["Meter added"]

    EDIT_BTN --> EDIT_FORM["Edit form<br/>(pre-filled)"]
    EDIT_FORM --> SAVE_EDIT["Save changes"]
    SAVE_EDIT --> SUCCESS
```

**How it works:**

- **Linkage is mandatory:** A meter must be linked to a specific Utility Account (Step 5). This link tells the system who to bill when a reading is submitted
- **1:1 relationship:** Typically, one meter links to one account
- If the account does not exist yet, the Owner must create it (Step 5) before or during the meter setup

---

### Step 4: Submit Meter Readings

#### 4.1 Main Flow

```mermaid
flowchart TD
    subgraph OWNER_ACTIONS ["Owner"]
        OPEN["Opens 'Submit Readings'"] --> SELECT["Selects meter and<br/>enters current reading"] --> SUBMIT["Submits reading"]
    end

    subgraph SYSTEM_ACTIONS ["System"]
        SUBMIT --> CALC["Calculates cost:<br/>Consumption × Tariff"]
        CALC --> CHECK_RESP{"Responsibility<br/>on this Account?"}
    end

    subgraph TENANT_PATH ["If Tenant Pays"]
        CHECK_RESP -->|"Tenant"| BILL_T["Bill sent to Tenant<br/>as pending payment"]
        BILL_T --> NOTIFY_T["Push to Tenant:<br/>'New Bill: 112,100 UZS'"]
    end

    subgraph OWNER_PATH ["If Owner Pays"]
        CHECK_RESP -->|"Owner"| BILL_O["Bill added to<br/>Owner's Payables"]
    end
```

**Submit Meter Reading form fields:**

- **Meter** — dropdown, required (list of active meters for this property)
- **Previous Reading** — optional (for reference)
- **Current Reading** — input, required
- **Reading Date** — date picker (defaults to today)
- **Note** — optional textarea

**How it works:**
- After calculating cost (Consumption × Tariff), the system checks the **responsibility setting** on the linked Utility Account
- **If Tenant pays:** Bill is sent to the tenant's app as a pending payment. Owner sees "Awaiting Tenant Payment"
- **If Owner pays:** Bill is added to the Owner's Payables (Step 9). Tenant sees "Paid by Landlord" (read-only, no Pay button)
- Readings can only be submitted for the current period (no older than 3 days)

---

### Step 5: Manage Utility Accounts (Лицевой Счет)

```mermaid
flowchart TD
    ACCOUNTS["Owner opens<br/>'Utility Accounts'"] --> LOAD["Fetch utility accounts<br/>for this property"]

    LOAD --> LIST["Existing Accounts:<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya — #12345<br/>  Pays: **Tenant**<br/>━━━━━━━━━━━━━━━━━━<br/>Sovuq suv — #888999<br/>  Pays: **Owner**<br/>━━━━━━━━━━━━━━━━━━"]

    LIST --> ADD["+ Add Account"]

    ADD --> PROVIDER["Select Provider<br/>(e.g. 'Sovuq Suv')"]

    PROVIDER --> INPUT_ACC["Enter Account Details:<br/>━━━━━━━━━━━━━━━━━━<br/>Account number: [__________]"]

    INPUT_ACC --> RESP_TOGGLE["**Payment Responsibility:**<br/>(•) Tenant (Default)<br/>( ) Owner (Landlord)"]

    RESP_TOGGLE --> VALIDATE["Validate via Paynet"]

    VALIDATE -->|"Valid"| SAVE["Save Account<br/>with Responsibility Settings"]
    VALIDATE -->|"Invalid"| NOT_FOUND["Account not found.<br/>Check number and try again."]
    NOT_FOUND --> INPUT_ACC

    SAVE --> SAVED["Account saved<br/>Visible to tenant"]
```

**How it works:**
- **Responsibility Toggle:** Defines who receives the bill. This is a required field when adding an account
  - **Tenant (default):** Bills go to the tenant's app as payable items
  - **Owner:** Bills stay in the owner's app for payment. Tenant sees them as "Paid by Landlord"
- This setting applies to **both** metered (Elektroenergiya, Tabiiy Gaz, Sovuq suv) and non-metered (Sovuq suv, Chiqindilarni olib ketish) accounts
- Each account number can only be linked once per provider per property (no duplicates)
- The owner can change responsibility at any time; existing debt transfers to the new payer's view

---

### Step 6: Billing Management (v1.1)

```mermaid
flowchart TD
    BILLING["Owner opens<br/>'Billing'"] --> LOAD["Load charges<br/>for selected month"]

    LOAD --> VIEW["Charges for Feb 2026<br/>━━━━━━━━━━━━━━━━━━"]

    VIEW --> METERED["Metered Charges<br/>(from meter readings × tariff)<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya: 112,100 UZS<br/>  380 kWh × 295 UZS/kWh<br/>  Status: Sent to tenant<br/>━━━━━━━━━━━━━━━━━━<br/>Sovuq suv: 45,000 UZS<br/>  15 m³ × 3,000 UZS/m³<br/>  Status: Sent to tenant"]

    VIEW --> NON_METERED["Non-Metered Charges<br/>(tariff × variable: Residents / Area / Volume)<br/>━━━━━━━━━━━━━━━━━━<br/>Chiqindilarni olib ketish: 25,000 UZS<br/>  5,000 UZS × 5 residents<br/>  Status: Sent to tenant<br/>━━━━━━━━━━━━━━━━━━<br/>Issiqlik ta'minoti: 80,000 UZS<br/>  2,000 UZS × 40 m²<br/>  Status: Sent to tenant"]

```

**How it works:**

- **Metered charges** are generated automatically when an owner submits a meter reading and a valid tariff exists: `consumption × tariff = cost`
- **Non-metered charges** are calculated by the billing engine based on service type: `tariff × variable` (e.g., number of residents or apartment area)
- Both charge types go directly to the assigned payer (Tenant or Owner) based on the **responsibility setting** on the linked Utility Account (Step 5)
- All charges appear in the payer's Utilities section as pending items

---

### Step 6.1: Non-Metered Settlement Flow

> **Context:** Non-metered utilities (Chiqindilarni olib ketish, Issiqlik ta'minoti, Mening uyim (XUJMSH), etc.) do not require meter readings. The billing engine automatically calculates charges based on the service type's calculation variable.

```mermaid
flowchart TD
    START["Non-metered billing<br/>triggered (monthly)"] --> DETERMINE["System determines<br/>calculation category<br/>based on service type"]

    DETERMINE --> CALC_TYPE{"Calculation<br/>Variable?"}

    CALC_TYPE -->|"Per Resident"| PER_RES["Tariff × Number of Residents<br/>━━━━━━━━━━━━━━━━━━<br/>e.g. Chiqindilarni olib ketish:<br/>5,000 UZS × 5 residents<br/>= 25,000 UZS"]
    CALC_TYPE -->|"Per Area (m²)"| PER_AREA["Tariff × Area<br/>━━━━━━━━━━━━━━━━━━<br/>e.g. Issiqlik ta'minoti:<br/>2,000 UZS × 40 m²<br/>= 80,000 UZS"]

    PER_RES --> CHARGE["Utility charge created<br/>(amount known)"]
    PER_AREA --> CHARGE

    CHARGE --> RESP_CHECK{"Responsibility<br/>on this Account?"}

    RESP_CHECK -->|"Tenant pays"| BILL_TENANT["Bill sent to Tenant<br/>as pending payment"]
    RESP_CHECK -->|"Owner pays"| BILL_OWNER["Bill added to<br/>Owner's Payables"]
```

**How it works:**

- Non-metered charges are generated **automatically** on a monthly cycle — no owner action required
- The billing engine selects the correct calculation variable based on the service type:
  - **Per Resident:** Chiqindilarni olib ketish, Mening uyim (XUJMSH)
  - **Per Area (m²):** Issiqlik ta'minoti, Issiq suv va issiqlik ta'minoti, Elektroenergiya
- After calculation, the charge is routed based on the **responsibility setting** on the linked Utility Account (Step 5)
- Payment follows the same flow as metered charges (Step 9 for Owner, or Tenant payment flow)

---

### Step 7: Tenant Utility Payment History (Owner View)

```mermaid
flowchart TD
    PAYMENTS["Owner opens<br/>'Payment History'"] --> FILTER["Filters:<br/>━━━━━━━━━━━━━━━━━━<br/>Property: [All / specific]<br/>Tenant: [All / specific]<br/>Status: [All / Paid / Pending / Failed]<br/>Date range: [From] — [To]<br/>Provider: [All / specific]"]

    FILTER --> LOAD["Fetch payment history<br/>with applied filters"]

    LOAD --> HISTORY["Payment History:<br/>━━━━━━━━━━━━━━━━━━<br/>Feb 2026<br/>Elektroenergiya — 112,100 UZS — Feb 3 — Paid<br/>  Paid by: Tenant (Paynet)<br/>Sovuq suv — 45,000 UZS — Feb 3 — Paid<br/>  Paid by: Tenant (auto-pay, Paynet)<br/>Tabiiy Gaz — 92,100 UZS — Pending<br/>  Due: Feb 10<br/>━━━━━━━━━━━━━━━━━━<br/>Jan 2026<br/>Elektroenergiya — 108,500 UZS — Jan 2 — Paid<br/>..."]

    HISTORY --> DETAIL["Tap payment → Receipt:<br/>━━━━━━━━━━━━━━━━━━<br/>• Transaction ID<br/>• Payment method<br/>• Date & time<br/>• Auto-pay: Yes/No"]

    HISTORY --> EXPORT_BTN["Download as PDF"]
```

---

### Step 8: Auto-Pay Oversight (Read-Only)

```mermaid
flowchart TD
    AUTOPAY["Owner opens<br/>'Auto-Pay Status'"] --> LOAD["Fetch tenant auto-pay<br/>info"]

    LOAD --> VIEW["Tenant Auto-Pay Info:<br/>━━━━━━━━━━━━━━━━━━<br/>Tenant: Тошматов Жасур<br/>━━━━━━━━━━━━━━━━━━<br/>Elektroenergiya #12345 — Active<br/>  Day: 1st, Amount: Full balance<br/>  Method: Paynet, Next: Mar 1<br/>━━━━━━━━━━━━━━━━━━<br/>Sovuq suv #67890 — Active<br/>  Day: 5th, Amount: Fixed 30,000<br/>  Method: Paynet, Next: Mar 5<br/>━━━━━━━━━━━━━━━━━━<br/>Tabiiy Gaz — No auto-pay<br/>Issiqlik ta'minoti — No auto-pay<br/>Chiqindilarni olib ketish — No auto-pay"]

    VIEW --> SUMMARY["Summary:<br/>2 of 5 accounts have auto-pay<br/>Coverage: 40%"]
```

**How it works:** This is a read-only view. The owner can see which utility accounts have auto-pay enabled by the tenant, but cannot modify or require auto-pay settings — that is entirely controlled by the tenant.

---

### Step 9: Owner Payment Flow

> **Context:** When Responsibility = Owner, or when an owner voluntarily chooses to pay a tenant's overdue bill, they use this flow. It mirrors the Tenant's payment flow (using the same Paynet integration) but occurs within the Owner's interface.

```mermaid
flowchart TD
    OPEN["Owner opens<br/>'Utilities'"] --> DASH["Dashboard showing:<br/>**My Payable Bills (3)**"]

    DASH --> LIST["1. Elektroenergiya (Apt 12): 50,000 UZS<br/>2. Issiqlik ta'minoti (Apt 12): 150,000 UZS<br/>3. Tabiiy Gaz (Apt 5): 20,000 UZS"]

    LIST --> SELECT["Owner taps a bill"]

    SELECT --> EDIT_AMT{"Edit Amount?"}
    EDIT_AMT -->|"Pay full balance"| CARD_CHOICE{"Card Selection"}
    EDIT_AMT -->|"Custom amount"| CUSTOM_AMT["Enter custom amount"] --> CARD_CHOICE

    CARD_CHOICE -->|"New card"| NEW_CARD["Enter Credit/Card Details<br/>(card number, expiry date)"]
    CARD_CHOICE -->|"Saved card"| SAVED_CARD["Select Saved Card"]

    NEW_CARD --> PAY_OPTS_NEW{"Payment Option"}
    PAY_OPTS_NEW -->|"One-time"| SAVE_CARD{"Save Card?"}
    SAVE_CARD -->|"Yes"| TOKENIZE["Tokenize & save card<br/>for future payments"] --> SEND_OTP
    SAVE_CARD -->|"No"| SEND_OTP
    PAY_OPTS_NEW -->|"Auto-pay"| SCHEDULE_NEW["Set Auto-Pay Schedule<br/>(day of month + amount)"]
    SCHEDULE_NEW --> AUTO_SAVE["Tokenize & save card &<br/>activate auto-pay"] --> SEND_OTP

    SAVED_CARD --> PAY_OPTS_SAVED{"Payment Option"}
    PAY_OPTS_SAVED -->|"One-time"| SEND_OTP
    PAY_OPTS_SAVED -->|"Auto-pay"| SCHEDULE_SAVED["Set Auto-Pay Schedule<br/>(day of month + amount)"] --> SEND_OTP

    SEND_OTP["System sends OTP<br/>to registered phone"]
    SEND_OTP --> ENTER_OTP["Owner enters OTP"]
    ENTER_OTP --> OTP_CHECK{"OTP Valid?"}

    OTP_CHECK -->|"Yes"| CONFIRM["Confirm Payment<br/>(amount, provider, account)"]
    OTP_CHECK -->|"No"| OTP_ERROR["Invalid OTP<br/>'Code is incorrect or expired'"]
    OTP_ERROR --> ENTER_OTP

    CONFIRM --> RECEIPT["Payment Receipt<br/>(Payer: Owner Name)"]
    RECEIPT --> UPDATE["Update Tenant View:<br/>'Paid by Owner'"]
```

**How it works:**

- Owner sees all bills where `responsibility = Owner` in their Payables
- **Same Paynet integration** as the tenant flow — card, OTP, receipt. No separate payment engine
- Receipt shows the Owner's name as payer; accessible to both Owner and Tenant

---

### Step 10: Tenant Changes

> What happens to utility accounts when tenants move in or out.

#### 10.1 Move-Out

When a lease ends, the system does **NOT** auto-assign bills to the Owner.

- Lease status → **Terminated**
- Tenant-assigned accounts → **Unassigned**
- Owner gets an alert:

> ⚠️ **Vacant Property (Apt 12)** — 3 accounts are unassigned. Choose: **[Take Responsibility]** or **[Assign to New Tenant]**

#### 10.2 Move-In

When creating a new lease, the Owner assigns utility responsibility:

1. Owner selects property
2. System shows linked accounts — Owner sets who pays:
   - Elektroenergiya #123 (Metered) → Tenant / Owner
   - Issiqlik ta'minoti #456 (Non-metered) → Tenant / Owner
3. Owner can change responsibility during the lease if needed
