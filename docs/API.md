# Backend API Guide

All HTTP endpoints below are prefixed with `/api/v1`. Authentication uses a bearer access token unless the endpoint is public. The generated OpenAPI document at `/docs` is the authoritative source for request and response schemas.

## Authentication and account

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | Public | Register a user account |
| POST | `/auth/login` | Public | Obtain access and refresh tokens |
| POST | `/auth/refresh` | Refresh token | Rotate a token pair |
| POST | `/auth/logout` | Authenticated | Revoke a refresh token |
| GET | `/auth/me` | Authenticated | Read current account |
| GET/PATCH | `/users/me` | Authenticated | Read or update own profile |
| PUT | `/users/me/language` | Authenticated | Save `en`, `ta`, or `hi` preference |
| GET | `/languages` | Public | List supported language codes |

## Astrology and consultations

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/astrology/chart?language=en` | Authenticated | Calculate Rasi/Navamsa, planets, and dasha data |
| GET | `/locations/search?q=...&language=en` | Public | Find a place and its coordinates |
| POST/GET | `/consultations` | User / participant | Book consultations or list the caller's sessions |
| PATCH | `/consultations/{consultation_id}` | Participant by role | Transition consultation state |
| POST | `/astrologers/apply` | User | Submit an astrologer application |
| GET | `/astrologers` | Public | Search or browse approved astrologers |
| GET/PATCH | `/astrologers/me` | Astrologer | Read or update own profile |

## Chat, calls, and payments

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST/GET | `/chat/{consultation_id}/messages` | Consultation participants | Send or list text and attachment messages |
| GET | `/chat/{consultation_id}/messages/{message_id}/attachment` | Consultation participants | Download a protected attachment |
| WebSocket | `/ws/chat/{consultation_id}?token=...` | Consultation participants | Receive and send live text messages |
| POST | `/calls/start` | Consultation participants | Record a call start |
| POST | `/calls/{call_id}/end` | Call participant | End a call and record its duration |
| POST/GET | `/payments` and `/payments/mine` | User / admin | Create or list payment records |
| PATCH | `/payments/{payment_id}/status` | Admin | Update payment status |
| POST | `/voice/text-to-speech` | Authenticated | Generate speech audio for supplied text |

Chat attachment requests are limited to 8 MiB. The message history omits base64 payloads; attachment bytes are retrieved from the protected attachment endpoint.

## Reports, reviews, and support

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/reports/generate` | Assigned astrologer | Generate a localized AI report and PDF for a completed consultation |
| GET | `/reports` | User, astrologer, or admin | List reports visible to the caller |
| POST | `/reports/{report_id}/share` | Assigned astrologer or admin | Share a draft with the client |
| GET | `/reports/{report_id}/pdf` | Authorized report participant | Download the generated PDF |
| POST | `/reports` | Assigned astrologer or admin | Save a manually authored report |
| POST/GET | `/reviews` and `/reviews/{astrologer_id}` | User / public | Submit or read astrologer reviews |
| POST/GET/PATCH | `/complaints` | User / admin | Create, list, and manage complaints |

Report generation accepts `language` (`en`, `ta`, or `hi`). If omitted, the account preference is used. The language is stored with the report and used for AI text, chart display labels, PDF headings, and PDF rendering. A Unicode script font and `uharfbuzz` are needed for correctly shaped Tamil and Hindi glyphs.

## Administration and health

- `GET /admin/dashboard`: administrator metrics.
- `GET /admin/astrologers/pending` and `PATCH /admin/astrologers/{id}/approval`: review applications.
- `GET /admin/users` and `PATCH /admin/users/{id}/active`: manage user access.
- `GET /health`: process health response (does not guarantee external AI-provider availability).
