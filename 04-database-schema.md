# Database Schema

All tables use PostgreSQL with the conventions defined below. Every column is listed with its exact type, constraints, and validation rules.

---

## Conventions

| Convention | Rule |
|-----------|------|
| Table names | Plural, snake_case: `real_estates`, `listing_requests` |
| Column names | Singular, snake_case: `tenant_id`, `created_at` |
| Primary key | `id uuid PRIMARY KEY DEFAULT gen_random_uuid()` |
| Foreign keys | Named: `fk_{table}_{column}`. Always has ON DELETE behavior |
| Indexes | Named: `ix_{table}_{column}`. Created for all FKs, `tenant_id`, `status`, `created_at` |
| Unique constraints | Named: `uq_{table}_{column}` |
| Check constraints | Named: `ck_{table}_{column}` |
| Soft delete | `is_deleted boolean NOT NULL DEFAULT false` on every table |
| Timestamps | `timestamptz` (with timezone), always UTC |
| Money | `bigint` in integer Som (UZS). Tiyin not in circulation. Never `decimal` or `float` |
| Enums | Stored as `smallint`. Mapped via application enum |
| Strings | Always `varchar(N)` with explicit max length. Never unbounded `text` |

---

## Schema: identity

### Table: users

Person identity. Not tied to any tenant.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| register_type | smallint | NO | - | - | - | - | 0=Phone, 1=EImzo, 2=OneId, 3=MyID, 4=GovID |
| first_name | varchar | YES | NULL | 100 | - | - | |
| last_name | varchar | YES | NULL | 100 | - | - | |
| middle_name | varchar | YES | NULL | 100 | - | - | |
| phone_number | varchar | YES | NULL | 20 | - | ix_users_phone_number | |
| pinfl | varchar | YES | NULL | 14 | - | ix_users_pinfl (UNIQUE) | 14-digit Uzbekistan personal ID (JSHSHIR). Required for E-Imzo signing, E-Ijara, contracts |
| tin | varchar | YES | NULL | 20 | - | - | INN/STIR (individual taxpayer ID) |
| myid_id | varchar | YES | NULL | 50 | - | ix_users_myid_id (UNIQUE) | MyID internal user identifier. Auto-filled from MyID KYC |
| passport_series | varchar | YES | NULL | 2 | - | - | e.g., "AA", "AB". Required for contract generation |
| passport_number | varchar | YES | NULL | 7 | - | - | 7-digit passport number. Required for contract generation |
| passport_issued_by | varchar | YES | NULL | 200 | - | - | Issuing IIB (MVD) office name |
| passport_issued_date | date | YES | NULL | - | - | - | Date of passport issuance |
| birth_date | date | YES | NULL | - | - | - | Required for E-Imzo cert matching and contract clauses |
| serial_number | varchar | YES | NULL | 50 | - | ix_users_serial_number (UNIQUE) | E-Imzo certificate serial |
| region_id | uuid | YES | NULL | - | regions(id) | ix_users_region_id | |
| district_id | uuid | YES | NULL | - | districts(id) | ix_users_district_id | |
| address | varchar | YES | NULL | 500 | - | - | Registered address (propiska) |
| object_name | varchar | YES | NULL | 500 | - | - | MinIO avatar key |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_users_created_at | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

> **Uzbekistan law note:** `pinfl`, `passport_series`, `passport_number`, and `birth_date` are required for: (1) lease contract generation (Uzbek Civil Code Art. 535), (2) E-Imzo digital signature verification (PINFL must match certificate), (3) E-Ijara lease registration. The system should prompt users to complete these fields before signing contracts.

**Unique constraints:** `uq_users_pinfl`, `uq_users_serial_number`  
**Global query filter:** `WHERE is_deleted = false`

---

### Table: companies

Tenant entity. Every user belongs to at least one company.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| owner_id | uuid | NO | - | - | users(id) ON DELETE RESTRICT | ix_companies_owner_id | User who created this tenant |
| name | varchar | NO | - | 200 | - | - | |
| tin | varchar | YES | NULL | 20 | - | ix_companies_tin (UNIQUE) | Organization INN/STIR (9 digits) |
| serial_number | varchar | YES | NULL | 50 | - | ix_companies_serial_number | E-Imzo cert serial |
| register_type | smallint | NO | 0 | - | - | - | 0=Phone, 1=EImzo, 2=OneId |
| mfo | varchar | YES | NULL | 5 | - | - | Bank MFO code (5 digits), required for DiBank |
| oked | varchar | YES | NULL | 5 | - | - | Economic activity classifier (5 digits), required for E-Ijara |
| bank_account | varchar | YES | NULL | 20 | - | - | Settlement account (20 digits), required for DiBank |
| bank_name | varchar | YES | NULL | 200 | - | - | Servicing bank name |
| legal_address | varchar | YES | NULL | 500 | - | - | Registered legal address (for contracts, E-Ijara) |
| region_id | uuid | YES | NULL | - | regions(id) | - | |
| district_id | uuid | YES | NULL | - | districts(id) | - | |
| address | varchar | YES | NULL | 500 | - | - | Physical/operational address |
| phone_number | varchar | YES | NULL | 20 | - | - | |
| object_name | varchar | YES | NULL | 500 | - | - | MinIO logo key |
| is_verified | boolean | NO | false | - | - | - | |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_companies_created_at | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Unique constraints:** `uq_companies_tin` (WHERE tin IS NOT NULL)  
**Global query filter:** `WHERE is_deleted = false`

> **Compliance note:** `tin`, `mfo`, `bank_account`, and `oked` are required for DiBank payment orders and E-Ijara lease registration. The system should prompt tenant owners to complete these fields during onboarding.

---

### Table: accounts

User-to-tenant bridge. One user can have multiple accounts (one per tenant).

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_accounts_tenant_id | ALWAYS companies.id |
| user_id | uuid | NO | - | - | users(id) ON DELETE RESTRICT | ix_accounts_user_id | |
| role_id | uuid | NO | - | - | roles(id) ON DELETE RESTRICT | ix_accounts_role_id | |
| type | smallint | NO | 0 | - | - | - | 0=Client, 1=Owner, 2=Agent |
| is_owner | boolean | NO | false | - | - | - | Is this user the company founder |
| is_default | boolean | NO | false | - | - | - | Default account for this user |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Unique constraints:** `uq_accounts_tenant_user` (tenant_id, user_id) — one account per user per tenant  
**Global query filter:** `WHERE is_deleted = false AND tenant_id = current_tenant_id`

---

### Table: roles

RBAC roles. System roles have tenant_id = NULL. Tenant-specific roles have tenant_id set.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | YES | NULL | - | companies(id) ON DELETE CASCADE | ix_roles_tenant_id | NULL = system role |
| name | varchar | NO | - | 100 | - | - | |
| type | smallint | NO | 0 | - | - | - | 0=System, 1=Client, 2=Owner |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

**Global query filter:** `WHERE is_deleted = false AND (tenant_id = current_tenant_id OR tenant_id IS NULL)`

---

### Table: permissions

System-wide permission definitions.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| module | varchar | NO | - | 50 | - | - | "identity", "building", "common" |
| name | varchar | NO | - | 100 | - | uq_permissions_name (UNIQUE) | "buildings:read", "leases:write" |
| description | varchar | YES | NULL | 500 | - | - | |
| is_active | boolean | NO | true | - | - | - | |

**No tenant filter.** Permissions are global.

---

### Table: role_permissions

Join table: which permissions each role has.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| role_id | uuid | NO | - | - | roles(id) ON DELETE CASCADE | ix_rp_role_id | |
| permission_id | uuid | NO | - | - | permissions(id) ON DELETE CASCADE | ix_rp_permission_id | |
| value | smallint | NO | 0 | - | - | - | 0=None, 1=Read, 2=Write, 3=Full |

**Unique constraints:** `uq_role_permissions_role_permission` (role_id, permission_id)

---

### Table: sessions

Active authentication sessions.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| account_id | uuid | NO | - | - | accounts(id) ON DELETE CASCADE | ix_sessions_account_id | |
| refresh_token | varchar | NO | - | 500 | - | ix_sessions_refresh_token (UNIQUE) | |
| refresh_token_expiry | timestamptz | NO | - | - | - | - | |
| device_id | varchar | YES | NULL | 200 | - | uq_sessions_account_device (account_id, device_id) | Stable device fingerprint. Required for mobile, NULL for admin web |
| device_name | varchar | YES | NULL | 200 | - | - | Human-readable: "iPhone 15 Pro", "Samsung Galaxy S24" |
| device_info | varchar | YES | NULL | 500 | - | - | User-Agent or OS version |
| ip_address | varchar | YES | NULL | 50 | - | - | |
| is_terminated | boolean | NO | false | - | - | - | |
| last_active_at | timestamptz | YES | NULL | - | - | - | Updated on token refresh |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: invitations

Invite a user to join a tenant.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| sender_id | uuid | NO | - | - | companies(id) ON DELETE CASCADE | ix_invitations_sender_id | Sending company |
| recipient_id | uuid | YES | NULL | - | users(id) ON DELETE SET NULL | ix_invitations_recipient_id | Known user |
| recipient_phone | varchar | YES | NULL | 20 | - | - | If user not yet registered |
| role_id | uuid | NO | - | - | roles(id) ON DELETE RESTRICT | - | Role to assign |
| content | varchar | YES | NULL | 1000 | - | - | Message |
| key | varchar | NO | - | 100 | - | uq_invitations_key (UNIQUE) | Accept key/code |
| status | smallint | NO | 0 | - | - | ix_invitations_status | 0=Sent,1=Received,2=Accepted,3=Canceled,4=Rejected |
| reason | varchar | YES | NULL | 500 | - | - | Rejection reason |
| expired_time | timestamptz | NO | - | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

## Schema: building

### Table: buildings

Physical building structure.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_buildings_tenant_id | |
| region_id | uuid | YES | NULL | - | regions(id) | ix_buildings_region_id | |
| district_id | uuid | YES | NULL | - | districts(id) | - | |
| number | varchar | NO | - | 50 | - | - | Building number/name |
| is_commercial | boolean | NO | false | - | - | - | |
| is_residential | boolean | NO | false | - | - | - | |
| is_renovated | boolean | NO | false | - | - | - | false=shell, true=has floors/rooms |
| total_area | real | YES | NULL | - | - | - | Square meters |
| floors_count | smallint | YES | NULL | - | - | - | |
| location | geometry(Point,4326) | YES | NULL | - | - | ix_buildings_location (GIST) | PostGIS |
| cadastral_number | varchar | YES | NULL | 20 | - | ix_buildings_cadastral | 14-digit (land) or 18-digit (building) cadastral ID for E-Ijara |
| address | varchar | YES | NULL | 500 | - | - | |
| status | smallint | NO | 1 | - | - | ix_buildings_status | 0=Draft,1=Active,2=Inactive,3=Blocked,4=Archived |
| moderation_status | smallint | NO | 0 | - | - | - | 0=None,1=InModeration,2=Accepted,3=Rejected,4=Blocked |
| moderation_note | varchar | YES | NULL | 1000 | - | - | |
| moderated_by | uuid | YES | NULL | - | users(id) | - | |
| moderated_at | timestamptz | YES | NULL | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_buildings_created_at | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Global query filter:** `WHERE is_deleted = false AND tenant_id = current_tenant_id`

---

### Table: floors

Floors within a renovated building.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_floors_tenant_id | |
| building_id | uuid | NO | - | - | buildings(id) ON DELETE CASCADE | ix_floors_building_id | |
| number | smallint | NO | - | - | - | - | Floor number |
| area | real | YES | NULL | - | - | - | Square meters |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

**Unique constraints:** `uq_floors_building_number` (building_id, number)  
**Global query filter:** `WHERE is_deleted = false AND tenant_id = current_tenant_id`

---

### Table: rooms

Rooms on a floor.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_rooms_tenant_id | |
| floor_id | uuid | NO | - | - | floors(id) ON DELETE CASCADE | ix_rooms_floor_id | |
| room_type_id | uuid | YES | NULL | - | room_types(id) | - | |
| number | varchar | NO | - | 20 | - | - | Room number |
| area | real | YES | NULL | - | - | - | |
| status | smallint | NO | 1 | - | - | - | 0=Draft,1=Active |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: real_estates

Property record. What is being managed, listed, and rented.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_re_tenant_id | Managing company |
| owner_id | uuid | NO | - | - | users(id) ON DELETE RESTRICT | ix_re_owner_id | Property owner (person) |
| real_estate_type_id | uuid | NO | - | - | real_estate_types(id) | - | |
| building_id | uuid | YES | NULL | - | buildings(id) ON DELETE SET NULL | ix_re_building_id | |
| floor_id | uuid | YES | NULL | - | floors(id) ON DELETE SET NULL | - | |
| room_id | uuid | YES | NULL | - | rooms(id) ON DELETE SET NULL | - | |
| renovation_id | uuid | YES | NULL | - | renovation_types(id) | - | |
| cadastral_number | varchar | YES | NULL | 50 | - | ix_re_cadastral (UNIQUE) | 14-digit (land) or 18-digit (building) cadastral ID. Required for E-Ijara lease registration |
| building_number | varchar | YES | NULL | 50 | - | - | |
| floor_number | smallint | YES | NULL | - | - | - | |
| number | varchar | YES | NULL | 50 | - | - | Apartment/unit number |
| total_area | real | YES | NULL | - | - | - | |
| living_area | real | YES | NULL | - | - | - | |
| ceiling_height | real | YES | NULL | - | - | - | |
| total_floors | smallint | YES | NULL | - | - | - | |
| rooms_count | smallint | YES | NULL | - | - | - | |
| region_id | uuid | YES | NULL | - | regions(id) | ix_re_region_id | |
| district_id | uuid | YES | NULL | - | districts(id) | - | |
| location | geometry(Point,4326) | YES | NULL | - | - | ix_re_location (GIST) | |
| address | varchar | YES | NULL | 500 | - | - | |
| status | smallint | NO | 0 | - | - | ix_re_status | 0=Draft,1=Active,2=Inactive,3=Blocked,4=Archived |
| moderation_status | smallint | NO | 0 | - | - | - | |
| moderation_note | varchar | YES | NULL | 1000 | - | - | |
| moderated_by | uuid | YES | NULL | - | users(id) | - | |
| moderated_at | timestamptz | YES | NULL | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_re_created_at | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Global query filter:** `WHERE is_deleted = false AND tenant_id = current_tenant_id`

---

### Table: real_estate_images

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE CASCADE | ix_rei_real_estate_id | |
| object_name | varchar | NO | - | 500 | - | - | MinIO key |
| sort_order | smallint | NO | 0 | - | - | - | |
| is_plan | boolean | NO | false | - | - | - | Floor plan vs photo |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: real_estate_amenities

Join table: real estate to amenity (replaces JSON array).

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE CASCADE | ix_rea_real_estate_id | |
| amenity_id | uuid | NO | - | - | amenities(id) ON DELETE CASCADE | ix_rea_amenity_id | |
| value | varchar | YES | NULL | 50 | - | - | Optional value (e.g. "2" for parking spots) |

**Unique constraints:** `uq_rea_real_estate_amenity` (real_estate_id, amenity_id)

---

### Table: units

Rentable units within a real estate.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_units_tenant_id | |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE CASCADE | ix_units_real_estate_id | |
| number | varchar | NO | - | 50 | - | - | |
| area | real | YES | NULL | - | - | - | |
| status | smallint | NO | 1 | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: listings

Published rental offer.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_listings_tenant_id | |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE RESTRICT | ix_listings_real_estate_id | |
| unit_id | uuid | YES | NULL | - | units(id) ON DELETE SET NULL | - | |
| listing_type | smallint | NO | 0 | - | - | - | 0=Rent (future: 1=Sale) |
| title | varchar | YES | NULL | 200 | - | - | |
| description | varchar | YES | NULL | 2000 | - | - | |
| price | bigint | NO | - | - | - | ix_listings_price | In integer Som (UZS) |
| currency | smallint | NO | 0 | - | - | - | 0=UZS, 1=USD |
| price_period | smallint | NO | 0 | - | - | - | 0=Monthly, 1=Daily, 2=Yearly |
| deposit_amount | bigint | YES | NULL | - | - | - | In integer Som (UZS) |
| min_lease_months | smallint | YES | NULL | - | - | - | |
| max_lease_months | smallint | YES | NULL | - | - | - | |
| available_from | date | YES | NULL | - | - | - | |
| is_negotiable | boolean | NO | false | - | - | - | |
| utilities_included | boolean | NO | false | - | - | - | |
| location | geometry(Point,4326) | YES | NULL | - | - | ix_listings_location (GIST) | |
| status | smallint | NO | 0 | - | - | ix_listings_status | 0=Draft,1=Active,2=Inactive,3=Booked,4=Rented,5=Archived |
| moderation_status | smallint | NO | 0 | - | - | - | |
| moderation_note | varchar | YES | NULL | 1000 | - | - | |
| moderated_by | uuid | YES | NULL | - | users(id) | - | |
| moderated_at | timestamptz | YES | NULL | - | - | - | |
| published_at | timestamptz | YES | NULL | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_listings_created_at | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Check constraints:** `ck_listings_price CHECK (price > 0)`  
**Global query filter:** `WHERE is_deleted = false AND tenant_id = current_tenant_id`  
**Public query filter (client browsing):** `WHERE status = 1 AND moderation_status = 2`

---

### Table: listing_requests

Client request to rent a listed property.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| listing_id | uuid | NO | - | - | listings(id) ON DELETE RESTRICT | ix_lr_listing_id | |
| owner_tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_lr_owner_tenant_id | Listing owner |
| client_tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_lr_client_tenant_id | Requesting party |
| client_user_id | uuid | NO | - | - | users(id) ON DELETE RESTRICT | - | Actual person |
| content | varchar | YES | NULL | 1000 | - | - | Message from client |
| status | smallint | NO | 0 | - | - | ix_lr_status | 0=Sent,1=Received,2=Accepted,3=Canceled,4=Rejected |
| reason | varchar | YES | NULL | 500 | - | - | Rejection reason |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

---

### Table: leases

Rental contract.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_leases_tenant_id | Owner company |
| client_tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_leases_client_tenant_id | Renter company |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE RESTRICT | ix_leases_real_estate_id | |
| unit_id | uuid | YES | NULL | - | units(id) ON DELETE SET NULL | - | |
| listing_id | uuid | NO | - | - | listings(id) ON DELETE RESTRICT | - | Source listing |
| listing_request_id | uuid | NO | - | - | listing_requests(id) ON DELETE RESTRICT | - | Source request |
| start_date | date | NO | - | - | - | - | |
| end_date | date | NO | - | - | - | - | |
| monthly_rent | bigint | NO | - | - | - | - | In integer Som (UZS) |
| deposit_amount | bigint | YES | NULL | - | - | - | In integer Som (UZS) |
| currency | smallint | NO | 0 | - | - | - | 0=UZS, 1=USD |
| payment_day | smallint | NO | 1 | - | - | - | Day of month (1-28) |
| status | smallint | NO | 0 | - | - | ix_leases_status | 0=Pending,1=Active,2=Inactive,3=Suspended,4=Revoked,5=Expired |
| contract_number | varchar | YES | NULL | 50 | - | uq_leases_contract_number | |
| contract_document_id | varchar | YES | NULL | 500 | - | - | MinIO key for generated PDF |
| notes | varchar | YES | NULL | 2000 | - | - | |
| **E-Imzo Signing** | | | | | | | |
| owner_signed_at | timestamptz | YES | NULL | - | - | - | When owner signed via E-Imzo |
| client_signed_at | timestamptz | YES | NULL | - | - | - | When client signed via E-Imzo |
| owner_signature_key | varchar | YES | NULL | 500 | - | - | MinIO key: PKCS#7 signature file (owner) |
| client_signature_key | varchar | YES | NULL | 500 | - | - | MinIO key: PKCS#7 signature file (client) |
| owner_signer_pinfl | varchar | YES | NULL | 14 | - | - | PINFL extracted from owner's E-Imzo certificate |
| client_signer_pinfl | varchar | YES | NULL | 14 | - | - | PINFL extracted from client's E-Imzo certificate |
| is_fully_signed | boolean | NO | false | - | - | - | True when both parties signed |
| signed_at | timestamptz | YES | NULL | - | - | - | Legacy/manual signing timestamp |
| **E-Ijara Registration** | | | | | | | |
| eijara_registration_id | varchar | YES | NULL | 100 | - | ix_leases_eijara | E-Ijara system registration ID |
| eijara_status | smallint | YES | NULL | - | - | - | 0=Submitted, 1=AwaitingLessee, 2=Registered, 3=Rejected, 4=Expired |
| eijara_submitted_at | timestamptz | YES | NULL | - | - | - | |
| eijara_registered_at | timestamptz | YES | NULL | - | - | - | |
| eijara_certificate_key | varchar | YES | NULL | 500 | - | - | MinIO key: QR-coded registration certificate PDF |
| terminated_at | timestamptz | YES | NULL | - | - | - | |
| termination_reason | varchar | YES | NULL | 500 | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

**Check constraints:** `ck_leases_monthly_rent CHECK (monthly_rent > 0)`, `ck_leases_payment_day CHECK (payment_day BETWEEN 1 AND 28)`, `ck_leases_dates CHECK (end_date > start_date)`

> **E-Ijara compliance:** Uzbekistan law requires all real estate lease agreements to be registered in the E-Ijara system within 3 business days of signing (Presidential Decree UP-60). Leases >1 year also require state registration at the cadastral office. The `eijara_status` field tracks this process.

---

### Table: lease_payments

Individual payment records for a lease.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| lease_id | uuid | NO | - | - | leases(id) ON DELETE CASCADE | ix_lp_lease_id | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_lp_tenant_id | |
| amount | bigint | NO | - | - | - | - | In integer Som (UZS) |
| currency | smallint | NO | 0 | - | - | - | |
| due_date | date | NO | - | - | - | ix_lp_due_date | |
| paid_date | date | YES | NULL | - | - | - | |
| payment_method | smallint | YES | NULL | - | - | - | 0=BankTransfer, 1=Card, 2=Cash |
| status | smallint | NO | 0 | - | - | ix_lp_status | 0=Pending, 1=Paid, 2=Overdue, 3=PartiallyPaid, 4=Canceled |
| external_id | varchar | YES | NULL | 200 | - | - | Payment gateway transaction ID |
| receipt_number | varchar | YES | NULL | 100 | - | - | |
| **Didox ESF (Fiscal Invoice)** | | | | | | | |
| didox_document_id | varchar | YES | NULL | 100 | - | ix_lp_didox | Didox.uz internal document ID |
| esf_number | varchar | YES | NULL | 50 | - | uq_lp_esf_number | Electronic fiscal invoice number (e.g., ESF-2026-0001234) |
| esf_status | smallint | YES | NULL | - | - | - | 0=Draft, 1=Signed, 2=Submitted, 3=Accepted, 4=Rejected |
| esf_signed_at | timestamptz | YES | NULL | - | - | - | When ESF was signed via E-Imzo EDS |
| mxik_code | varchar | YES | NULL | 20 | - | - | MXIK product code, default "06310.100" (rental) |
| notes | varchar | YES | NULL | 500 | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

> **Didox compliance:** All B2B lease payments require an electronic fiscal invoice (ESF) submitted to Soliq.uz via Didox. ESF is auto-generated when payment status changes to Paid (for BankTransfer and Card methods). The `mxik_code` defaults to `06310.100` (real estate rental services).

---

### Table: meters

Utility meters attached to any scope level.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_meters_tenant_id | |
| meter_type_id | uuid | NO | - | - | meter_types(id) | - | |
| scope | smallint | NO | - | - | - | - | 0=Building, 1=RealEstate, 2=Room, 3=Unit |
| scope_id | uuid | NO | - | - | - | ix_meters_scope | Polymorphic FK |
| serial_number | varchar | YES | NULL | 100 | - | - | |
| name | varchar | YES | NULL | 200 | - | - | |
| installation_date | date | YES | NULL | - | - | - | |
| last_verified_date | date | YES | NULL | - | - | - | |
| is_active | boolean | NO | true | - | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: meter_readings

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| meter_id | uuid | NO | - | - | meters(id) ON DELETE CASCADE | ix_mr_meter_id | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_mr_tenant_id | |
| previous_value | numeric(12,3) | NO | 0 | - | - | - | |
| current_value | numeric(12,3) | NO | - | - | - | - | |
| consumption | numeric(12,3) | NO | - | - | - | - | Auto: current - previous |
| reading_date | date | NO | - | - | - | ix_mr_reading_date | |
| recorded_by | uuid | NO | - | - | users(id) | - | Who submitted |
| photo_object_name | varchar | YES | NULL | 500 | - | - | Proof photo MinIO key |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: meter_tariffs

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| meter_id | uuid | NO | - | - | meters(id) ON DELETE CASCADE | ix_mt_meter_id | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | - | |
| rate_per_unit | numeric(10,2) | NO | - | - | - | - | Price per kWh/m3/etc |
| currency | smallint | NO | 0 | - | - | - | |
| effective_from | date | NO | - | - | - | - | |
| effective_until | date | YES | NULL | - | - | - | NULL = ongoing |
| is_active | boolean | NO | true | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

---

### Table: wishlists

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_wishlists_tenant_id | |
| user_id | uuid | NO | - | - | users(id) ON DELETE CASCADE | ix_wishlists_user_id | |
| listing_id | uuid | NO | - | - | listings(id) ON DELETE CASCADE | ix_wishlists_listing_id | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |

**Unique constraints:** `uq_wishlists_user_listing` (user_id, listing_id)

---

### Table: delegations

Agent authorization to manage property on behalf of owner.

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_delegations_tenant_id | Owner company |
| agent_tenant_id | uuid | NO | - | - | companies(id) ON DELETE RESTRICT | ix_delegations_agent_tenant_id | Agent company |
| real_estate_id | uuid | NO | - | - | real_estates(id) ON DELETE RESTRICT | ix_delegations_real_estate_id | |
| unit_id | uuid | YES | NULL | - | units(id) ON DELETE SET NULL | - | |
| valid_from | date | NO | - | - | - | - | |
| valid_until | date | YES | NULL | - | - | - | NULL = indefinite |
| contract_document_id | varchar | YES | NULL | 500 | - | - | MinIO key |
| contract_number | varchar | YES | NULL | 50 | - | - | |
| commission_type | smallint | NO | 0 | - | - | - | 0=Percent, 1=Fixed |
| commission_value | bigint | NO | 0 | - | - | - | Percent*100 or integer Som |
| require_owner_approval | boolean | NO | true | - | - | - | |
| status | smallint | NO | 0 | - | - | ix_delegations_status | 0=Active, 1=Suspended, 2=Revoked, 3=Expired |
| notes | varchar | YES | NULL | 1000 | - | - | |
| revoked_at | timestamptz | YES | NULL | - | - | - | |
| revoked_reason | varchar | YES | NULL | 500 | - | - | |
| is_deleted | boolean | NO | false | - | - | - | |
| created_at | timestamptz | NO | now() | - | - | - | |
| updated_at | timestamptz | YES | NULL | - | - | - | |

---

## Schema: common

### Table: regions

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| is_active | boolean | NO | true | - | - | - | |

### Table: region_translates

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| region_id | uuid | NO | - | - | regions(id) ON DELETE CASCADE | ix_rt_region_id | |
| language_code | varchar | NO | - | 5 | - | - | "uz", "ru", "en" |
| name | varchar | NO | - | 200 | - | - | |

**Unique constraints:** `uq_rt_region_language` (region_id, language_code)

### Table: districts

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| region_id | uuid | NO | - | - | regions(id) ON DELETE CASCADE | ix_districts_region_id | |
| is_active | boolean | NO | true | - | - | - | |

### Table: district_translates

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| district_id | uuid | NO | - | - | districts(id) ON DELETE CASCADE | ix_dt_district_id | |
| language_code | varchar | NO | - | 5 | - | - | |
| name | varchar | NO | - | 200 | - | - | |

**Unique constraints:** `uq_dt_district_language` (district_id, language_code)

---

## Schema: building (reference data)

### Table: real_estate_types

| Column | Type | Nullable | Default | Max Length | FK | Index |
|--------|------|----------|---------|------------|-----|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK |
| is_active | boolean | NO | true | - | - | - |

### Table: real_estate_type_translates

| Column | Type | Nullable | Default | Max Length | FK | Index |
|--------|------|----------|---------|------------|-----|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK |
| real_estate_type_id | uuid | NO | - | - | real_estate_types(id) ON DELETE CASCADE | ix |
| language_code | varchar | NO | - | 5 | - | - |
| name | varchar | NO | - | 200 | - | - |

Same pattern applies to: `room_types`, `renovation_types`, `amenity_categories`, `amenities`, `meter_types`. Each has a base table with `id` + `is_active` and a `_translates` table with `language_code` + `name`.

---

## Schema: core

### Table: audit_logs

| Column | Type | Nullable | Default | Max Length | FK | Index | Notes |
|--------|------|----------|---------|------------|-----|-------|-------|
| id | uuid | NO | gen_random_uuid() | - | - | PK | |
| tenant_id | uuid | YES | NULL | - | - | ix_al_tenant_id | NULL for system actions |
| user_id | uuid | YES | NULL | - | - | ix_al_user_id | |
| entity_type | varchar | NO | - | 100 | - | ix_al_entity_type | "Lease", "Listing", etc |
| entity_id | uuid | NO | - | - | - | ix_al_entity_id | |
| action | smallint | NO | - | - | - | - | 0=Create, 1=Update, 2=Delete, 3=StatusChange |
| old_values | jsonb | YES | NULL | - | - | - | Previous state |
| new_values | jsonb | YES | NULL | - | - | - | New state |
| ip_address | varchar | YES | NULL | 50 | - | - | |
| user_agent | varchar | YES | NULL | 500 | - | - | |
| created_at | timestamptz | NO | now() | - | - | ix_al_created_at | |

**No soft delete.** Audit logs are immutable.  
**No tenant filter.** Audit logs are queried by admin only with explicit filters.  
**Retention:** Configurable per tenant, default 2 years.

---

## Microservice-Owned Schemas

The following tables are **not** in the main `maydon-api` PostgreSQL database. They belong to separate microservice databases and are documented in [10-microservices.md](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/10-microservices.md):

| Service | Database | Tables |
|---------|----------|--------|
| payment-service | PostgreSQL (own) | `payment_transactions`, `bank_configurations`, `didox_invoices` |
| notification-service | PostgreSQL (own) | `device_tokens`, `notification_templates`, `notification_deliveries` |
| audit-log-service | ClickHouse | `audit_events` |
| analytics-service | ClickHouse | `domain_events` + materialized views (`listing_metrics`, `revenue_metrics`, `occupancy_metrics`) |
