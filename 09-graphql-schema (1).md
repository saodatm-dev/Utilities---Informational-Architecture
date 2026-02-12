# GraphQL Schema

This document defines the read-only GraphQL layer for client-facing listing search and property browsing.

**Endpoint:** `/graphql`  
**Auth:** Optional. Anonymous users see public data. Authenticated users get personalization (wishlist status).

---

## 1. Rationale

### Why GraphQL for This Layer

The listing browse and search experience on mobile has these characteristics:

1. **Variable data needs.** The listing card on search results needs 8 fields. The listing detail screen needs 40+ fields including nested building, amenities, images, and owner info. REST forces either over-fetching or multiple round-trips.

2. **Mobile bandwidth sensitivity.** Uzbekistan mobile networks average 15-25 Mbps (4G). Reducing payload size by requesting only needed fields directly improves load times.

3. **Filter complexity.** Listing search supports 15+ filter parameters. REST query strings become unwieldy. GraphQL input types are more expressive and self-documenting.

4. **Rapid iteration.** Mobile screens change frequently during product development. GraphQL allows frontend to adjust data requirements without backend deployment.

### Why Not GraphQL for Everything

| Concern | REST Advantage |
|---------|---------------|
| Mutations | One endpoint = one transaction = one audit log entry |
| Authorization | Per-endpoint RBAC is simpler than per-field/per-resolver |
| File uploads | Native multipart support, no custom spec needed |
| Caching | HTTP cache headers work out of the box |
| Error handling | HTTP status codes provide semantic meaning |
| Admin operations | Lower complexity, easier to audit |

**Rule:** All mutations, all admin operations, all authentication, and all file uploads stay on REST.

---

## 2. Schema Definition

```graphql
# ================================================================
# Entry Points
# ================================================================

type Query {
  """Search and browse active listings with filters and pagination."""
  listings(filter: ListingFilter, pagination: PaginationInput!): ListingConnection!

  """Get a single listing by ID. Returns null if not found or not active."""
  listing(id: ID!): Listing

  """List all active regions."""
  regions: [Region!]!

  """List districts within a region."""
  districts(regionId: ID!): [District!]!

  """List all active real estate types."""
  realEstateTypes: [RealEstateType!]!

  """List all amenity categories with their amenities."""
  amenityCategories: [AmenityCategory!]!

  """List all active meter types."""
  meterTypes: [MeterType!]!

  """Get renovation type options."""
  renovationTypes: [RenovationType!]!
}


# ================================================================
# Listing Types
# ================================================================

type ListingConnection {
  edges: [ListingEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ListingEdge {
  cursor: String!
  node: Listing!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Listing {
  id: ID!
  title: String
  description: String
  listingType: ListingType!
  price: Long!
  currency: Currency!
  pricePeriod: PricePeriod!
  depositAmount: Long
  minLeaseMonths: Int
  maxLeaseMonths: Int
  availableFrom: Date
  isNegotiable: Boolean!
  utilitiesIncluded: Boolean!
  publishedAt: DateTime

  realEstate: RealEstate!
  location: GeoPoint
  address: String
  region: Region
  district: District
  images: [ListingImage!]!
  owner: ListingOwner!

  """Only populated when the request includes a valid JWT."""
  isWishlisted: Boolean
}

type ListingImage {
  id: ID!
  url: String!
  sortOrder: Int!
  isPlan: Boolean!
}

type ListingOwner {
  companyName: String!
  isVerified: Boolean!
  """Phone number is only visible in listing detail, not in search results."""
  phoneNumber: String
}


# ================================================================
# Real Estate Types
# ================================================================

type RealEstate {
  id: ID!
  type: RealEstateType!
  totalArea: Float
  livingArea: Float
  ceilingHeight: Float
  roomsCount: Int
  totalFloors: Int
  floorNumber: Int
  number: String
  cadastralNumber: String
  renovation: RenovationType
  building: Building
  amenities: [Amenity!]!
}

type Building {
  id: ID!
  number: String
  isCommercial: Boolean!
  isResidential: Boolean!
  isRenovated: Boolean!
  floorsCount: Int
  address: String
  region: Region
  district: District
}


# ================================================================
# Reference Data Types
# ================================================================

type Region {
  id: ID!
  name: String!
}

type District {
  id: ID!
  regionId: ID!
  name: String!
}

type RealEstateType {
  id: ID!
  name: String!
}

type RenovationType {
  id: ID!
  name: String!
}

type AmenityCategory {
  id: ID!
  name: String!
  amenities: [Amenity!]!
}

type Amenity {
  id: ID!
  name: String!
  category: AmenityCategory!
  """Amenity value specific to the real estate, e.g. '2' for parking spots."""
  value: String
}

type MeterType {
  id: ID!
  name: String!
  unit: String!
}


# ================================================================
# Scalar Types
# ================================================================

"""64-bit integer for monetary values (integer Som (UZS))."""
scalar Long

"""ISO 8601 date string: YYYY-MM-DD"""
scalar Date

"""ISO 8601 datetime string: YYYY-MM-DDTHH:mm:ssZ"""
scalar DateTime

type GeoPoint {
  latitude: Float!
  longitude: Float!
}


# ================================================================
# Enums
# ================================================================

enum ListingType {
  RENT
}

enum Currency {
  UZS
  USD
}

enum PricePeriod {
  MONTHLY
  DAILY
  YEARLY
}

enum ListingSortField {
  PRICE
  PUBLISHED_AT
  AREA
  ROOMS_COUNT
  DISTANCE
}

enum SortDirection {
  ASC
  DESC
}


# ================================================================
# Input Types
# ================================================================

input ListingFilter {
  """Filter by region."""
  regionId: ID

  """Filter by district."""
  districtId: ID

  """Filter by real estate type."""
  realEstateTypeId: ID

  """Minimum price in integer Som (UZS) (inclusive)."""
  priceMin: Long

  """Maximum price in integer Som (UZS) (inclusive)."""
  priceMax: Long

  """Filter by currency."""
  currency: Currency

  """Minimum total area in square meters."""
  areaMin: Float

  """Maximum total area in square meters."""
  areaMax: Float

  """Minimum number of rooms."""
  roomsCountMin: Int

  """Maximum number of rooms."""
  roomsCountMax: Int

  """Filter by amenities (AND logic: listing must have all specified)."""
  amenityIds: [ID!]

  """Filter commercial properties."""
  isCommercial: Boolean

  """Filter residential properties."""
  isResidential: Boolean

  """Center latitude for proximity search."""
  latitude: Float

  """Center longitude for proximity search."""
  longitude: Float

  """Radius in kilometers for proximity search. Requires latitude and longitude."""
  radiusKm: Float

  """Sort field."""
  sortBy: ListingSortField

  """Sort direction."""
  sortDirection: SortDirection
}

input PaginationInput {
  """Cursor-based: fetch items after this cursor."""
  after: String

  """Cursor-based: fetch items before this cursor."""
  before: String

  """Number of items to fetch (max: 50)."""
  first: Int

  """Number of items to fetch from the end."""
  last: Int
}
```

---

## 3. Query Examples

### Search Results (Mobile Listing Card)

```graphql
query SearchListings($filter: ListingFilter, $pagination: PaginationInput!) {
  listings(filter: $filter, pagination: $pagination) {
    edges {
      cursor
      node {
        id
        title
        price
        currency
        pricePeriod
        isNegotiable
        isWishlisted
        realEstate {
          type { name }
          totalArea
          roomsCount
        }
        images(first: 1) {
          url
        }
        region { name }
        district { name }
        publishedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

**Variables:**

```json
{
  "filter": {
    "regionId": "uuid",
    "priceMin": 300000000,
    "priceMax": 800000000,
    "currency": "UZS",
    "roomsCountMin": 2,
    "sortBy": "PRICE",
    "sortDirection": "ASC"
  },
  "pagination": {
    "first": 20
  }
}
```

### Listing Detail (Full Screen)

```graphql
query ListingDetail($id: ID!) {
  listing(id: $id) {
    id
    title
    description
    price
    currency
    pricePeriod
    depositAmount
    minLeaseMonths
    maxLeaseMonths
    availableFrom
    isNegotiable
    utilitiesIncluded
    isWishlisted
    publishedAt
    realEstate {
      type { id name }
      totalArea
      livingArea
      ceilingHeight
      roomsCount
      totalFloors
      floorNumber
      number
      renovation { name }
      building {
        number
        isCommercial
        isResidential
        floorsCount
        address
      }
      amenities {
        name
        category { name }
        value
      }
    }
    location { latitude longitude }
    address
    region { id name }
    district { id name }
    images {
      id
      url
      sortOrder
      isPlan
    }
    owner {
      companyName
      isVerified
      phoneNumber
    }
  }
}
```

---

## 4. Resolver Data Sources

| Resolver | Data Source | Notes |
|----------|-----------|-------|
| `listings` | PostgreSQL (read replica) | Uses PostGIS for proximity queries |
| `listing` | PostgreSQL (read replica) | Single lookup by PK |
| `realEstate` | Joined in listing query | Eager-loaded via EF Include |
| `building` | Joined in listing query | Eager-loaded |
| `amenities` | Joined via `real_estate_amenities` | Eager-loaded |
| `images` | Joined via `real_estate_images` | Sorted by `sort_order` |
| `owner` | Joined from `companies` via `tenant_id` | Only public fields |
| `isWishlisted` | Separate query per listing | Batch-loaded using DataLoader |
| `regions` | Redis cache (TTL: 24 hours) | Reference data, rarely changes. Uses Redis Static tier from [03-api-standards](file:///Users/agreeing/Documents/GitHub/maydon-api/docs/03-api-standards.md) |
| `districts` | Redis cache (TTL: 24 hours) | Reference data. Invalidated via domain event |
| `realEstateTypes` | Redis cache (TTL: 24 hours) | Reference data |
| `amenityCategories` | Redis cache (TTL: 24 hours) | Contains nested amenities |

---

## 5. Performance Rules

1. **Query depth limit:** Maximum 5 levels of nesting
2. **Query complexity limit:** Maximum 500 complexity points per query
3. **Pagination limit:** `first` and `last` capped at 50
4. **Batch loading:** All nested collections use DataLoader to prevent N+1
5. **Read replica:** All GraphQL queries run against the PostgreSQL read replica
6. **Response caching:** Persisted queries with cache headers (5 minutes for search, 1 minute for detail)
7. **Introspection:** Disabled in production

---

## 6. Error Handling

GraphQL errors follow the standard `errors` array format:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Listing not found.",
      "path": ["listing"],
      "extensions": {
        "code": "NOT_FOUND"
      }
    }
  ]
}
```

Error codes:

| Code | Description |
|------|-------------|
| `NOT_FOUND` | Requested resource does not exist or is not public |
| `VALIDATION_ERROR` | Invalid filter parameters |
| `QUERY_TOO_COMPLEX` | Query exceeds complexity limit |
| `DEPTH_EXCEEDED` | Query exceeds depth limit |
| `RATE_LIMITED` | Too many requests |
