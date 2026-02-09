# Tech Stack

## Runtime and Framework

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Runtime | .NET | 10 | Long-term support, performance, cross-platform |
| Web Framework | ASP.NET Core Minimal APIs | 10 | Endpoint routing, middleware pipeline |
| ORM | Entity Framework Core | 10 | Database access, migrations, query filters |
| Mediator | MediatR | 12.x | CQRS command/query dispatch, pipeline behaviors |
| Validation | FluentValidation | 11.x | Request validation in MediatR pipeline |
| Serialization | System.Text.Json | built-in | JSON serialization, source generators for performance |
| Spatial | NetTopologySuite | 2.x | PostGIS geometry types (Point, Polygon) for property locations |
| API Docs | Swagger / OpenAPI | built-in | Auto-generated API documentation |
| Background Jobs | Hangfire or Quartz.NET | latest | Lease expiration, payment reminders, scheduled tasks |

## Database

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Primary Database | PostgreSQL | 16+ | Relational data, PostGIS for geospatial queries |
| Cache | Redis | 7.x | Session cache, rate limiting, frequently accessed reference data |
| Search (Phase 2) | Elasticsearch | 8.x | Full-text listing search, geospatial proximity queries |
| Analytics (Phase 2) | ClickHouse | latest | High-volume read analytics, dashboards, reporting |

### Why PostgreSQL

- Native PostGIS extension for geospatial property search (radius, bounding box)
- Row-Level Security (RLS) for database-enforced tenant isolation
- JSONB for flexible metadata without sacrificing query performance
- Mature EF Core provider (Npgsql) with full feature coverage
- Strong ecosystem in Uzbekistan hosting providers

## Object Storage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Object Storage | MinIO (S3-compatible) | Property images, floor plans, contract documents, avatar photos |
| CDN (Phase 2) | CloudFront or nginx proxy | Image delivery optimization for mobile clients |

### File Naming Convention

All uploaded files are renamed to UUID on upload. Original filename is never stored in the object key.

```
{bucket}/{tenant_id}/{entity_type}/{entity_id}/{uuid}.{extension}
```

Example: `maydon/550e8400.../real-estate/7c9e6679.../a1b2c3d4.webp`

## Authentication and Security

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Auth Tokens | JWT (RS256) | Stateless authentication, claim-based authorization |
| Authorization | ASP.NET Core Policy Auth | Native `IAuthorizationHandler` + `PermissionRequirement`. See [ADR-007](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/02-architecture-decisions.md) |
| Identity Providers | E-Imzo, OneID, MyID, GovID | Uzbekistan national identity verification. E-Imzo = digital signature (EDS), OneID = OAuth2 SSO, MyID = biometric facial KYC, GovID = government OAuth2 |
| OTP | Custom + SMS Gateway | Phone number verification |
| Password Hashing | N/A | No password-based auth. All auth via E-Imzo, OneID, MyID, GovID, or OTP |
| Rate Limiting | Redis + ASP.NET Rate Limiter | Per-IP and per-tenant rate limiting |

## Messaging, Events, and Real-Time

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Internal Events | MediatR Notifications | Domain events within the monolith (synchronous) |
| Message Broker (Phase 2) | RabbitMQ | Async events to microservices (payment, notification, audit) |
| Real-Time (Phase 2) | ASP.NET Core SignalR | WebSocket push to mobile (React Native) and admin (Next.js). Redis backplane for multi-pod. See [ADR-008](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/02-architecture-decisions.md) |
| Inter-Service Sync (Phase 3+) | gRPC (`Grpc.AspNetCore` / `google.golang.org/grpc`) | Proto-first typed contracts between .NET monolith and Go microservices. See [ADR-009](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/02-architecture-decisions.md) |

### Why RabbitMQ

- Simpler operations than Kafka for the current scale
- Native .NET client (MassTransit or RabbitMQ.Client)
- Sufficient for event-driven communication between 4-5 services
- Upgrade path to Kafka if analytics throughput demands it

## Mobile

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React Native (Bare workflow) | 0.76+ | Cross-platform iOS + Android |
| Navigation | React Navigation | 7.x | Stack, tab, drawer navigation |
| State Management | TanStack Query (React Query) | 5.x | Server state, caching, background refresh |
| Local State | Zustand | 5.x | Client-side state (auth tokens, UI preferences) |
| Maps | react-native-maps | latest | Property location display, search by area |
| Animations | react-native-reanimated | 3.x | Smooth UI transitions, gesture-driven interactions |
| Push Notifications | Firebase Cloud Messaging | latest | Lease reminders, payment due, request status updates |
| Image Handling | react-native-fast-image | latest | Cached property image loading |
| i18n | i18next + react-i18next | latest | Uzbek (uz), Russian (ru) localization |

### Why React Native (Bare Workflow)

- Single codebase for iOS and Android reduces development cost
- Bare workflow allows native module access (E-Imzo SDK, biometrics, background location)
- Large talent pool in Uzbekistan market
- Performance sufficient for property browsing, image galleries, and form-heavy workflows
- Code sharing with future web client via React

## Admin Panel

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js | 15.x | SSR for SEO (public listing pages), admin dashboard |
| UI Library | shadcn/ui + Radix | Accessible, customizable component library |
| State | TanStack Query | Server state management |
| Charts | Recharts | Dashboard analytics visualization |
| Table | TanStack Table | Data grids for admin entity management |
| Auth | NextAuth.js | Admin session management |

## Frontend Libraries & Conventions

> Shared libraries and usage patterns across both Mobile (React Native) and Admin (Next.js). For detailed code examples, see the Code Style sections in [03-api-standards.md](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/03-api-standards.md).

### Validation — Zod

| Property | Value |
|----------|-------|
| Package | `zod` ^3.23 |
| Used by | Mobile + Admin |
| Rule | **Zod-first**: Define Zod schema, then infer TypeScript type via `z.infer<typeof Schema>`. Never create types manually. |

**3 usage patterns:**

| Pattern | Location | Example |
|---------|----------|---------|
| API response validation | `shared/lib/schemas/` | Parse API responses to catch backend contract breaks early |
| Form validation | `features/{name}/schemas/` | Validate user input before mutation |
| Environment config | `shared/config/env.ts` | Parse `process.env` at startup (fail fast on missing vars) |

### Server State — TanStack Query

| Property | Mobile | Admin |
|----------|--------|-------|
| Package | `@tanstack/react-query` ^5 | Same |
| DevTools | `@tanstack/react-query-devtools` | Same |
| Query keys | Hierarchical factory pattern (see `03-api-standards` → TanStack Query) | Same |
| `staleTime` | 4-tier system (static/warm/fresh/realtime) | Same |

**Mandatory pattern:** All `useQuery` / `useMutation` calls are wrapped in custom hooks inside `features/{name}/hooks/`. No inline query calls in components.

### Data Grids — TanStack Table (Admin only)

| Property | Value |
|----------|-------|
| Package | `@tanstack/react-table` ^8 |
| Column visibility | Persisted to `localStorage`, RBAC-controlled (super-admin sees tenant column) |
| Server-side pagination | Offset for admin tables; `page`, `page_size`, `sort_by`, `sort_direction` |

### Client State — Zustand (Mobile only)

| Property | Value |
|----------|-------|
| Package | `zustand` ^5 |
| Persistence | `zustand/middleware` + MMKV (encrypted) |
| Stores | `useAuthStore`, `useUIStore`, `useOfflineStore` |
| Rule | **Never store server data in Zustand.** If it comes from an API → TanStack Query. |

### Shared NPM Packages

| Package | Purpose | Both Platforms |
|---------|---------|----------------|
| `axios` | HTTP client with interceptors (token refresh, tenant header) | ✅ |
| `zod` | Runtime validation, type inference | ✅ |
| `@tanstack/react-query` | Server state | ✅ |
| `react-hook-form` + `@hookform/resolvers` | Form state + Zod integration | ✅ |
| `date-fns` | Date formatting (Uzbek locale) | ✅ |
| `i18next` + `react-i18next` | i18n (uz, ru, en) | ✅ |
| `zustand` + `react-native-mmkv` | Client state (encrypted persistence) | Mobile |
| `@tanstack/react-table` | Data grids | Admin |
| `recharts` | Dashboard charts | Admin |

> For folder structure details, see ADR-010 in [02-architecture-decisions.md](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/02-architecture-decisions.md).



## Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Application packaging |
| Orchestration | Kubernetes (K8s) | Production deployment, scaling, health checks |
| CI/CD | GitHub Actions | Automated build, test, deploy pipeline |
| Secrets | HashiCorp Vault | API keys, database credentials, JWT signing keys |
| Monitoring | Prometheus + Grafana | Metrics collection and dashboards |
| Logging | Serilog + Seq (or ELK) | Structured logging with correlation IDs |
| Tracing (Phase 2) | OpenTelemetry + Jaeger | Distributed tracing across services |

## Development Tools

| Tool | Purpose |
|------|---------|
| EditorConfig + .editorconfig | Consistent code formatting across team |
| Roslyn Analyzers | Static code analysis, style enforcement |
| Husky.Net | Pre-commit hooks for linting and format checks |
| Docker Compose | Local development environment (PostgreSQL, Redis, MinIO, RabbitMQ) |

## Version Policy

- All NuGet packages pinned to exact versions in `.csproj`
- Dependency updates reviewed monthly
- Major version upgrades require team review and migration plan
- .NET runtime upgraded within 3 months of new LTS release

---

## NuGet Package Manifest

Core packages required across the solution:

| Package | Purpose | Layer |
|---------|---------|-------|
| `Npgsql.EntityFrameworkCore.PostgreSQL` | PostgreSQL EF Core provider + PostGIS + `UseXminAsConcurrencyToken` | Infrastructure |
| `MediatR` | CQRS command/query dispatch, pipeline behaviors | Application |
| `FluentValidation.AspNetCore` | Request validation via MediatR pipeline | Application |
| `Minio` | S3-compatible object storage client | Infrastructure |
| `StackExchange.Redis` | Redis cache, rate limiting, idempotency store | Infrastructure |
| `HotChocolate.AspNetCore` | GraphQL server (Phase 2, read-only listing layer) | API |
| `MassTransit.RabbitMQ` | Message broker abstraction (Phase 2) | Infrastructure |
| `Polly` | Resilience: retry, circuit breaker, timeout | Infrastructure |
| `Serilog.Sinks.Seq` | Structured logging to Seq | Infrastructure |
| `NetTopologySuite` | PostGIS geometry types (Point, Polygon) | Domain |
| `Swashbuckle.AspNetCore` | OpenAPI / Swagger generation | API |

---

## Gotenberg — PDF Generation Service

Contract PDFs and document generation use **Gotenberg** — a Docker-based, stateless REST API that converts HTML to pixel-perfect PDFs via headless Chromium.

| Property | Value |
|----------|-------|
| Type | Docker sidecar service |
| Default port | `3000` |
| Engines | Chromium (HTML/CSS/JS → PDF), LibreOffice (DOCX/XLSX → PDF) |
| Image | `gotenberg/gotenberg:8` |

### Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/forms/chromium/convert/html` | POST | HTML template → PDF (contract generation) |
| `/forms/chromium/convert/url` | POST | URL → PDF (report snapshots) |
| `/forms/pdfengines/merge` | POST | Merge multiple PDFs into one |
| `/forms/pdfengines/convert` | POST | Convert to PDF/A (1b, 2b, 3b) + PDF/UA for archival |
| `/health` | GET | Health check |

### Contract PDF Workflow

1. Backend renders an HTML contract template (Razor view or Scriban) with dynamic lease data
2. HTML + CSS + fonts sent to Gotenberg via `POST /forms/chromium/convert/html`
3. Gotenberg returns the PDF binary stream
4. PDF stored in MinIO: `{bucket}/{tenant_id}/contracts/{lease_id}/{uuid}.pdf`
5. Optional: convert to PDF/A-3b for long-term archival via `/forms/pdfengines/convert`

### Docker Compose

```yaml
services:
  gotenberg:
    image: gotenberg/gotenberg:8
    ports:
      - "3000:3000"
    environment:
      - GOTENBERG_API_TIMEOUT=60s
    restart: unless-stopped
```

### Zero-Transfer Pipeline

Gotenberg supports fetching documents from and uploading results directly to S3/MinIO, eliminating intermediate disk I/O. Use the `Download From` webhook headers to write the converted PDF directly to MinIO.

---

## EF Core Configuration Deep-Dive

### Connection Pool

```csharp
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString, npgsql =>
    {
        npgsql.EnableRetryOnFailure(
            maxRetryCount: 3,
            maxRetryDelay: TimeSpan.FromSeconds(5),
            errorCodesToAdd: null);
        npgsql.UseNetTopologySuite();
        npgsql.MigrationsHistoryTable("__ef_migrations", "core");
    }));
```

### Concurrency Token (xmin)

Every entity that supports optimistic concurrency uses PostgreSQL's `xmin` system column:

```csharp
// In entity configuration
builder.Entity<Lease>().UseXminAsConcurrencyToken();

// In entity class
public uint Version { get; set; } // maps to xmin
```

On concurrent modification, `SaveChangesAsync()` throws `DbUpdateConcurrencyException` → API returns `409 Conflict` with current ETag.

### Global Query Filters

```csharp
// Soft delete filter (applied to all entities)
builder.Entity<BaseEntity>().HasQueryFilter(e => !e.IsDeleted);

// Tenant isolation filter
builder.Entity<TenantScopedEntity>()
    .HasQueryFilter(e => e.TenantId == _currentTenantId);
```

### Split Queries

Default to split queries for includes with multiple collections to avoid cartesian explosion:

```csharp
options.UseNpgsql(conn, o => o.UseQuerySplittingBehavior(
    QuerySplittingBehavior.SplitQuery));
```

### RLS Connection Interceptor

```csharp
public class TenantConnectionInterceptor : DbConnectionInterceptor
{
    public override async Task ConnectionOpenedAsync(
        DbConnection connection, ConnectionEndEventData eventData, CancellationToken ct)
    {
        await using var cmd = connection.CreateCommand();
        cmd.CommandText = $"SET LOCAL app.tenant_id = '{_tenantId}'";
        await cmd.ExecuteNonQueryAsync(ct);
    }
}
```

`SET LOCAL` is scoped to the current transaction — automatically cleared when the connection returns to the pool.

---

## MinIO / Object Storage Deep-Dive

### Bucket Strategy

| Environment | Bucket | Notes |
|-------------|--------|-------|
| Production | `maydon-prod` | Versioning enabled, lifecycle policies |
| Staging | `maydon-staging` | Mirrors prod structure |
| Local Development | `maydon-dev` | Docker compose, no lifecycle |

### Object Key Pattern

```
{bucket}/{tenant_id}/{entity_type}/{entity_id}/{uuid}.{ext}
```

Examples:
```
maydon-prod/550e8400.../real-estate/7c9e6679.../a1b2c3d4.webp
maydon-prod/550e8400.../contracts/9f8e7d6c.../b2c3d4e5.pdf
maydon-prod/550e8400.../avatars/3a4b5c6d.../c3d4e5f6.jpg
```

### Image Upload Pipeline

1. **Magic byte validation** — verify file header matches declared MIME type (don't trust `Content-Type` header)
2. **File size check** — reject files > 10 MB
3. **EXIF stripping** — remove GPS and camera metadata (privacy)
4. **Image resize** — generate thumbnails (200px, 600px) + original
5. **UUID rename** — original filename never stored in object key
6. **Upload to MinIO** — stream directly, no intermediate disk

### Presigned URLs

**For image delivery (default):**
- Generate presigned GET URLs with configurable TTL (default: 1 hour)
- Returned in API responses as `image_url` fields
- Client fetches directly from MinIO — no load on API server

**For authenticated document downloads (contracts, PDFs):**
- Stream through API with `Authorization` check
- `Content-Disposition: attachment; filename="contract.pdf"`
- No presigned URL — access control enforced per request

---

## Payment Stack

The platform does **not** use Multicard. Payments are routed through:

### DiBank — B2B Payment Orders

| Property | Value |
|----------|-------|
| Provider | [dibank.uz](https://dibank.uz) |
| Purpose | Corporate banking: automated payment orders and bank statement retrieval |
| Auth | E-Imzo PKCS#7 digital signatures + API key |
| Document types | 101 (payment order), 102 (24/7), 103 (top-up), 104 (treasury), 105 (budget), 107 (payroll) |

### Uzcard SV-Gate — Direct Card API

| Property | Value |
|----------|-------|
| Provider | UZCARD Payment System |
| Integration | Partner PIS ↔ SV-Gate API ↔ UZCARD |
| Requirements | Partnership agreement, OTP verification, InfoSec compliance |
| Note | Uzbek debit cards have no CVV |

### Payme — Merchant + Subscribe API

| Property | Value |
|----------|-------|
| Provider | [paycom.uz](https://paycom.uz) |
| Protocols | Merchant API (one-time), Subscribe API (recurring/autopay) |
| Card types | Uzcard + Humo |
| Confirmation | OTP (not 3DS) |

### Paynet — Payment Aggregator

| Property | Value |
|----------|-------|
| Provider | [paynet.uz](https://paynet.uz) |
| Purpose | Aggregator for 200+ service providers: utility payments (electricity, water, gas, internet), government fees, and B2B settlement |
| Integration | REST API + callback webhook |
| Key feature | Single integration to pay for all utility services — no per-provider contract |
| Utility billing | Used for tenant utility charges (electricity via "Hududiy elektr tarmoqlari", gas via "Hududgazta'minot", water via local providers) |

### Kapitalbank — Card Acquiring + Banking

| Property | Value |
|----------|-------|
| Provider | [kapitalbank.uz](https://kapitalbank.uz) |
| Purpose | Second largest bank in Uzbekistan. Full-stack acquiring: card payments, P2P, salary projects |
| Card types | Uzcard, Humo, Visa, Mastercard |
| Integration | REST API with HMAC authentication |
| Key features | International card acceptance (Visa/MC), installment payments ("nasiya"), corporate card issuing |
| Note | Primary option for international tenants/owners who need Visa/Mastercard |

### Payment Routing by Use Case

| Use Case | Provider | Method |
|----------|----------|--------|
| Tenant rent (B2B wire) | DiBank | Payment order (type 101), EDS-signed |
| Tenant rent (local card) | Payme / Uzcard SV-Gate | One-time card payment, OTP |
| Tenant rent (international card) | Kapitalbank | Visa/Mastercard 3DS |
| Recurring autopay | Payme Subscribe API | Tokenized card, monthly |
| Deposit / prepayment | DiBank or card | Configurable per tenant |
| Utility bills (electricity, gas, water) | Paynet | Aggregated utility payment |
| Installment payments | Kapitalbank | "Nasiya" installment plan |

