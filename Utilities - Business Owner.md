# Utilities — Owner (Business) User Flow & API Design

> **Module:** `utility` (new module, extends `building` module)  
> **Actor:** Owner / Agent (`typ: "Owner"` or `typ: "Agent"` in JWT)  
> **Existing Backend:** Meter, MeterType, MeterTariff, MeterReading domain models in `Building.Domain`  
> **Integration:** Paynet (utility aggregator), payment-service (Go microservice)  
> **Related:** [Tenant Utilities Flow](./utilities-payment-userflow.md)

---

## Design Decisions (Confirmed)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Scope | All owner features: meter management, readings, лицевой счет pre-fill, billing, payment history, auto-pay visibility |
| 2 | Feature tiers | **v1:** Meter CRUD, readings, лицевой счет pre-fill, payment history, dashboard. **v1.1:** Tariff management (owner-level), billing engine |
| 3 | Meter readings actor | Owner submits; `submitted_by` field tracks who; system sends overdue reminders |
| 4 | Billing automation | Auto-calculated charges (reading × tariff) go directly to tenant. Only manual charges have dispute window |
| 5 | Payment visibility | Owner sees all statuses (Paid, Pending, Failed, Refunded) + aggregate dashboard + PDF export |
| 6 | Navigation | Dashboard is landing page → drill down to per-property views |
| 7 | Auto-pay oversight | Owner can see tenant auto-pay status; cannot require tenants to set up auto-pay |
| 8 | Architecture | New utility accounts/billing tables; reuses existing `meters`, `meter_readings`, `meter_tariffs`, `meter_types` tables |

---

## 1. High-Level Owner Flow Overview

```mermaid
flowchart TD
    START["Owner opens<br/>'Utilities' section"] --> DASHBOARD["Utilities Dashboard<br/>(aggregate view across<br/>all properties)"]

    DASHBOARD --> ALERTS["Action Items<br/>• Overdue meter readings<br/>• Unpaid utility debts<br/>• Accounts needing validation"]
    DASHBOARD --> STATS["Summary Stats<br/>• Total collected this month<br/>• Outstanding balance<br/>• Properties with issues"]
    DASHBOARD --> PROP_LIST["Property List<br/>(all owned real estates<br/>with utility status)"]

    PROP_LIST --> SELECT_PROP["Select Property"]

    SELECT_PROP --> PROP_VIEW["Property Utility Overview<br/>━━━━━━━━━━━━━━━━━━<br/>Meters | Accounts | Billing<br/>Payments | Auto-Pay Status"]

    PROP_VIEW --> METERS["Manage Meters<br/>(Add / Edit / Deactivate)"]
    PROP_VIEW --> READINGS["Submit Readings<br/>(monthly meter readings)"]
    PROP_VIEW --> ACCOUNTS["Pre-fill Accounts<br/>(лицевой счет for tenants)"]
    PROP_VIEW --> PAYMENTS["Payment History<br/>(all tenant payments)"]
    PROP_VIEW --> AUTOPAY["Auto-Pay Status<br/>(tenant configuration)"]

    METERS --> READINGS
    READINGS --> PAYMENTS

    PAYMENTS --> EXPORT["Export PDF Report"]
```

---

## 2. Detailed User Flow — Step-by-Step

### Step 1: Utilities Dashboard (Landing Page)

```mermaid
flowchart TD
    OPEN["Owner opens<br/>'Utilities'"] --> LOAD["Load dashboard<br/>summary"]

    LOAD --> DASH["Dashboard View"]

    DASH --> SECTION_A["Action Required<br/>━━━━━━━━━━━━━━━━━━<br/>3 meter readings overdue<br/>2 tenants with unpaid debts<br/>1 лицевой счет invalid"]

    DASH --> SECTION_B["Monthly Summary<br/>━━━━━━━━━━━━━━━━━━<br/>Total Utility Charges: 2,450,000 UZS<br/>Collected: 1,800,000 UZS<br/>Outstanding: 650,000 UZS<br/>Properties: 8 active"]

    DASH --> SECTION_C["Properties<br/>━━━━━━━━━━━━━━━━━━<br/>Apt 12, Building A — All paid<br/>Apt 5, Building B — 50,000 UZS due<br/>Apt 8, Building C — Overdue 3 days<br/>Office 3, Building D — All paid<br/>..."]

    SECTION_A --> TAP_ACTION["Tap action item<br/>→ navigate to relevant screen"]
    SECTION_C --> TAP_PROP["Tap property<br/>→ Property Utility Overview"]
```

---

### Step 2: Property Utility Overview (Drill-Down)

```mermaid
flowchart TD
    PROP["Property selected:<br/>'Apartment 12, Building A-1'<br/>Tenant: Тошматов Жасур"] --> TABS["Navigation Tabs"]

    TABS --> T_METERS["Meters<br/>(3 active meters)"]
    TABS --> T_ACCOUNTS["Accounts<br/>(5 лицевой счетов)"]
    TABS --> T_BILLING["Billing<br/>(Feb charges)"]
    TABS --> T_PAYMENTS["Payments<br/>(12 this year)"]
    TABS --> T_AUTOPAY["Auto-Pay<br/>(2 of 5 active)"]

    T_METERS --> METERS_VIEW["Meter List:<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity — SN: E-12345<br/>  Last reading: Feb 1 — 12,450 kWh<br/>Water (cold) — SN: W-67890<br/>  Last reading: Feb 1 — 234 m³<br/>Gas — SN: G-11111<br/>  Last reading: Jan 28 — 1,890 m³"]

    T_ACCOUNTS --> ACC_VIEW["Utility Accounts:<br/>━━━━━━━━━━━━━━━━━━<br/>Tabiiy Gaz — #1234567890<br/>Elektroenergiya — #0987654321<br/>Elektroenergiya Yur — #5555666677<br/>Suyultirilgan Gaz — #4443332211<br/>Sovuq suv — #9998887766<br/>Chiqindilarni olib ketish — #1112223344<br/>Tabiiy Gaz Yur — #6667778899<br/>Issiq suv va issiqlik ta'minoti — #3334445566<br/>Mening uyim (XUJMSH) — #888999<br/>Ichimlik Suvi Yur — #2221110099<br/>Issiqlik ta'minoti — #7776665544<br/>Issiq suv va issiqlik ta'minoti Yur — #5554443322"]

    T_BILLING --> BILL_VIEW["Charges for Feb 2026:<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity: 238,340 UZS (auto)<br/>Water: 45,000 UZS (auto)<br/>Gas: 92,100 UZS (auto)<br/>Plumbing repair: 150,000 UZS (manual)<br/>━━━━━━━━━━━━━━━━━━<br/>Total: 525,440 UZS"]
```

---

### Step 3: Manage Meters

```mermaid
flowchart TD
    METERS["Owner opens<br/>'Meters' tab"] --> LIST["Fetch meters<br/>for this property"]

    LIST --> VIEW["Meter List:<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity (Individual)<br/>  Лицевой счет: 1234567890<br/>  Installed: 2024-01-15<br/>  Next verification: 2028-01-15<br/>  Status: Active<br/>━━━━━━━━━━━━━━━━━━<br/>Cold Water<br/>  Лицевой счет: 9876543210<br/>  Installed: 2023-06-01<br/>  Status: Active"]

    VIEW --> ADD_BTN["+ Add Meter"]
    VIEW --> EDIT_BTN["Edit Meter"]
    VIEW --> DEACTIVATE["Deactivate Meter"]

    ADD_BTN --> ADD_FORM["Add Meter Form:<br/>━━━━━━━━━━━━━━━━━━<br/>Meter Type: [dropdown]<br/>  (Electricity, Gas, Water...)<br/>Лицевой счет: [input]<br/>Installation Date: [date]<br/>Verification Date: [date]<br/>Next Verification: [date]<br/>Initial Reading: [number]"]

    ADD_FORM --> VALIDATE_FORM{"Valid?"}
    VALIDATE_FORM -->|"Yes"| SAVE["Save meter<br/>to property"]
    VALIDATE_FORM -->|"No"| ERROR["Validation errors"]
    ERROR --> ADD_FORM

    SAVE --> SUCCESS["Meter added<br/>Appears in meter list"]

    EDIT_BTN --> EDIT_FORM["Edit form<br/>(pre-filled)"]
    EDIT_FORM --> SAVE_EDIT["Save changes"]
    SAVE_EDIT --> SUCCESS

    DEACTIVATE --> CONFIRM_DEACT{"Confirm<br/>deactivation?"}
    CONFIRM_DEACT -->|"Yes"| DO_DEACT["Deactivate meter"]
    CONFIRM_DEACT -->|"No"| VIEW
```

**How it works:**
- Each meter belongs to a specific property and has a type (Electricity, Gas, Water, etc.), лицевой счет (billing account number), installation/verification dates, and active status
- Meter types include localized names, measurement units, and linked tariffs
- The owner can add new meters, edit existing ones, or deactivate meters that are no longer in use

---

### Step 4: Submit Meter Readings

```mermaid
flowchart TD
    READINGS["Owner opens<br/>'Submit Readings'"] --> LOAD["Fetch active meters<br/>for this property"]

    LOAD --> METER_LIST["Active Meters:<br/>Select meter to submit reading"]

    METER_LIST --> SELECT["Owner selects meter:<br/>'Electricity — 1234567890'"]

    SELECT --> PREV["Show Previous Reading:<br/>━━━━━━━━━━━━━━━━━━<br/>Last reading: 12,450 kWh<br/>Date: Jan 28, 2026<br/>Consumption: 380 kWh"]

    PREV --> INPUT["Enter New Reading:<br/>━━━━━━━━━━━━━━━━━━<br/>Current reading: [_____]<br/>Reading date: [today]<br/>Note: [optional]"]

    INPUT --> CALC{"Reading ><br/>previous?"}

    CALC -->|"Yes"| PREVIEW["Preview:<br/>━━━━━━━━━━━━━━━━━━<br/>Previous: 12,450 kWh<br/>Current: 12,830 kWh<br/>Consumption: 380 kWh<br/>━━━━━━━━━━━━━━━━━━<br/>Tariff: 295 UZS/kWh<br/>Estimated cost: 112,100 UZS"]

    CALC -->|"No"| WARN["Reading is lower<br/>than previous value.<br/>Check and correct."]
    WARN --> INPUT

    PREVIEW --> SUBMIT["Submit reading"]

    SUBMIT --> SUCCESS["Reading submitted<br/>Charge auto-generated<br/>and sent to tenant"]

    SUBMIT --> REMINDER_FLOW

    subgraph REMINDER_FLOW ["Overdue Reminder System"]
        CRON["Scheduled Job<br/>(daily at 08:00 UTC+5)"] --> CHECK["Check meters with<br/>no reading this month"]
        CHECK --> DAY5{"Day 5 of<br/>month?"}
        DAY5 -->|"Yes"| NOTIFY["Push notification:<br/>'Submit meter readings<br/>for Apt 12, Building A'"]
        DAY5 -->|"No"| DAY10{"Day 10?"}
        DAY10 -->|"Yes"| URGENT["Urgent notification:<br/>'Meter reading overdue<br/>for 3 properties'"]
        DAY10 -->|"No"| SKIP["Skip check"]
    end
```

**How it works:**
- The system tracks who submitted each reading (owner or tenant)
- Consumption is automatically calculated as the difference between the current and previous readings
- If a tariff is set for the meter type, the system auto-generates a charge and sends it directly to the tenant
- Readings can only be submitted for the current period (no older than 3 days)

---

### Step 5: Pre-Fill Лицевой Счет (Utility Accounts)

```mermaid
flowchart TD
    ACCOUNTS["Owner opens<br/>'Utility Accounts'"] --> LOAD["Fetch utility accounts<br/>for this property"]

    LOAD --> LIST["Existing Accounts:<br/>━━━━━━━━━━━━━━━━━━<br/>ЭЛЕКТРИЧЕСТВО — #1234567890<br/>  Added by: Owner (you)<br/>  Balance: 50,000 UZS<br/>━━━━━━━━━━━━━━━━━━<br/>HOA 'Мой дом' — #888999<br/>  Added by: Tenant<br/>  Balance: 0 (paid up)<br/>━━━━━━━━━━━━━━━━━━<br/>+ Add Account"]

    LIST --> ADD["+ Add Account"]
    LIST --> EDIT_LABEL["Edit Label"]
    LIST --> DELETE_ACC["Delete Account"]

    ADD --> CATEGORY["Select Category:<br/>Resource Supply<br/>Property Management<br/>Ancillary Services"]

    CATEGORY --> PROVIDER["Select Provider<br/>from available list"]

    PROVIDER --> INPUT_ACC["Enter Account Details:<br/>━━━━━━━━━━━━━━━━━━<br/>Account number: [__________]<br/>Label: [e.g. 'Main electricity']"]

    INPUT_ACC --> VALIDATE_BVM["Validate account<br/>via Paynet"]

    VALIDATE_BVM -->|"Valid"| FOUND["Account Found:<br/>━━━━━━━━━━━━━━━━━━<br/>Provider: ЭЛЕКТРИЧЕСТВО<br/>Holder: Тошматов Жасур<br/>Address: Чиланзар 12<br/>Balance: 50,000 UZS"]
    VALIDATE_BVM -->|"Invalid"| NOT_FOUND["Account not found.<br/>Check number and try again."]
    NOT_FOUND --> INPUT_ACC

    FOUND --> SAVE["Save account<br/>(added by owner)"]

    SAVE --> SAVED["Account saved<br/>Visible to tenant"]
```

**How it works:**
- Accounts added by the owner are automatically visible to any tenant with an active lease on the property
- Accounts added by the tenant are visible to the owner in read-only mode
- The owner can only delete accounts they created, not ones added by tenants
- Each account number can only be linked once per provider per property (no duplicates)

---

### Step 6: Billing Management (v1.1)

```mermaid
flowchart TD
    BILLING["Owner opens<br/>'Billing'"] --> LOAD["Load charges<br/>for selected month"]

    LOAD --> VIEW["Charges for Feb 2026<br/>━━━━━━━━━━━━━━━━━━"]

    VIEW --> AUTO_SECTION["Auto-Calculated Charges<br/>(from meter readings × tariff)<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity: 112,100 UZS<br/>  380 kWh × 295 UZS/kWh<br/>  Status: Sent to tenant<br/>━━━━━━━━━━━━━━━━━━<br/>Water: 45,000 UZS<br/>  15 m³ × 3,000 UZS/m³<br/>  Status: Sent to tenant"]

    VIEW --> MANUAL_SECTION["Manual Charges<br/>━━━━━━━━━━━━━━━━━━<br/>Plumbing repair: 150,000 UZS<br/>  Status: Pending (3-day dispute window)<br/>  Tenant notified: Feb 5<br/>  Dispute deadline: Feb 8"]

    VIEW --> ADD_CHARGE["+ Add Manual Charge"]

    ADD_CHARGE --> CHARGE_FORM["Manual Charge Form:<br/>━━━━━━━━━━━━━━━━━━<br/>Description: [input]<br/>Amount: [number] UZS<br/>Category: [dropdown]<br/>  • Repair / Maintenance<br/>  • Cleaning<br/>  • Other<br/>Attach photo: [optional]"]

    CHARGE_FORM --> SUBMIT_CHARGE["Submit manual charge"]

    SUBMIT_CHARGE --> NOTIFY_TENANT["System notifies tenant:<br/>'New charge: Plumbing repair<br/>150,000 UZS. Dispute within<br/>3 days if incorrect.'"]

    NOTIFY_TENANT --> DISPUTE_CHECK{"Tenant disputes<br/>within 3 days?"}

    DISPUTE_CHECK -->|"No"| CONFIRMED["Charge confirmed<br/>Added to tenant's<br/>utility balance"]
    DISPUTE_CHECK -->|"Yes"| DISPUTED["Charge disputed<br/>Owner receives notification<br/>to resolve with tenant"]
    DISPUTED --> RESOLVE{"Owner resolves"}
    RESOLVE -->|"Adjust"| ADJUST["Modify charge amount"]
    RESOLVE -->|"Cancel"| CANCEL["Cancel charge"]
    RESOLVE -->|"Confirm original"| CONFIRMED
```

**How it works:**
- **Auto charges** are generated automatically when a meter reading is submitted and a valid tariff exists — they go directly to the tenant with no approval needed (based on objective data: reading × tariff)
- **Manual charges** follow a different process: owner creates a charge → tenant is notified → tenant has 3 days to dispute → if no dispute, the charge is auto-confirmed
- All charges appear in the tenant's Utilities section as pending items

---

### Step 7: Tenant Utility Payment History (Owner View)

```mermaid
flowchart TD
    PAYMENTS["Owner opens<br/>'Payment History'"] --> FILTER["Filters:<br/>━━━━━━━━━━━━━━━━━━<br/>Property: [All / specific]<br/>Tenant: [All / specific]<br/>Status: [All / Paid / Pending / Failed]<br/>Date range: [From] — [To]<br/>Type: [Utility / Manual]"]

    FILTER --> LOAD["Fetch payment history<br/>with applied filters"]

    LOAD --> HISTORY["Payment History:<br/>━━━━━━━━━━━━━━━━━━<br/>Feb 2026<br/>Electricity — 112,100 UZS — Feb 3 — Paid<br/>  Paid by: Tenant (Payme)<br/>Water — 45,000 UZS — Feb 3 — Paid<br/>  Paid by: Tenant (auto-pay, Click)<br/>Gas — 92,100 UZS — Pending<br/>  Due: Feb 10<br/>Plumbing — 150,000 UZS — Disputed<br/>  Tenant filed dispute Feb 6<br/>━━━━━━━━━━━━━━━━━━<br/>Jan 2026<br/>Electricity — 108,500 UZS — Jan 2 — Paid<br/>..."]

    HISTORY --> DETAIL["Tap payment → Receipt:<br/>━━━━━━━━━━━━━━━━━━<br/>• Transaction ID<br/>• Paynet transaction ID<br/>• Payment method<br/>• Date & time<br/>• Provider confirmation<br/>• Auto-pay: Yes/No"]

    HISTORY --> EXPORT_BTN["Export PDF"]

    EXPORT_BTN --> EXPORT["Generate PDF report"]

    EXPORT --> PDF["Downloaded:<br/>'Utility_Payments_Feb_2026.pdf'"]
```

---

### Step 8: Auto-Pay Oversight (Read-Only)

```mermaid
flowchart TD
    AUTOPAY["Owner opens<br/>'Auto-Pay Status'"] --> LOAD["Fetch tenant auto-pay<br/>configurations"]

    LOAD --> VIEW["Tenant Auto-Pay Configuration:<br/>━━━━━━━━━━━━━━━━━━<br/>Tenant: Тошматов Жасур<br/>━━━━━━━━━━━━━━━━━━<br/>Electricity #12345 — Active<br/>  Day: 1st, Amount: Full balance<br/>  Method: Payme, Next: Mar 1<br/>━━━━━━━━━━━━━━━━━━<br/>Water #67890 — Active<br/>  Day: 5th, Amount: Fixed 30,000<br/>  Method: Click, Next: Mar 5<br/>━━━━━━━━━━━━━━━━━━<br/>Gas — No auto-pay<br/>HOA — No auto-pay<br/>Intercom — No auto-pay"]

    VIEW --> SUMMARY["Summary:<br/>2 of 5 accounts have auto-pay<br/>Coverage: 40%"]
```

**How it works:** This is a read-only view. The owner can see which utility accounts have auto-pay enabled by the tenant, but cannot modify or require auto-pay settings — that is entirely controlled by the tenant.


