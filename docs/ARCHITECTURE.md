# Backend Architecture

```text
Browser client
  | HTTP JSON + bearer access token
  v
FastAPI app (app/main.py)
  |-- CORS and error handling
  |-- /api/v1 routers (app/api/v1)
  |-- /ws/chat WebSocket router
  |-- authentication and role dependencies (app/middleware)
  |-- domain services (app/services)
  |-- MongoDB client (app/config/database.py)
  `-- external providers: Gemini/OpenAI, geocoder, speech
```

## Request flow

1. `app/main.py` connects to MongoDB and registers the API and chat socket routers.
2. An API module validates the request with Pydantic and uses `current_user` or a role guard where required.
3. Domain calculations or provider calls live in `app/services`; database records are read/written through the shared database module.
4. `public_document` serializes stored documents without exposing MongoDB-specific identifiers directly.

## Role boundaries

- `USER` actions operate on the caller's profile, bookings, payments, reviews, complaints, and assigned consultation conversations.
- `ASTROLOGER` actions are scoped to the astrologer profile attached to the authenticated account and its consultations/reports.
- `ADMIN` routes provide approvals, user controls, dashboards, and moderation actions.
- Chat history, sockets, and attachment downloads independently verify consultation membership.

## Data collections

The current API uses MongoDB collections for users, refresh tokens, astrologers, consultations, messages, calls, payments, reports, reviews, and complaints. Related model definitions are in `app/models`; route validation schemas are in `app/schemas`.

## Generated reports

The report endpoint resolves the explicit language or account preference, calculates a localized chart, asks the selected AI provider for a report in that language, renders a branded PDF, then stores report metadata and PDF bytes. The PDF endpoint checks user/astrologer/admin visibility before returning the saved bytes. Language selection is captured at generation time; an existing report is not silently regenerated when an account preference later changes.
