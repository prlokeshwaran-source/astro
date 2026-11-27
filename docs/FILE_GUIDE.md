# Backend File Guide

This index describes the responsibilities of the backend source files. Add a short entry here when a new module becomes part of the application.

## Application and routing

| File | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI app, startup/shutdown lifecycle, CORS, health route, API/WebSocket mounting |
| `app/api/router.py` | Registers versioned API feature routers |
| `app/api/__init__.py` | API package marker |
| `app/api/v1/__init__.py` | Version 1 API package marker |
| `app/websocket/chat.py` | Authenticated chat socket, membership checks, room manager, live broadcasts |
| `app/websocket/__init__.py` | WebSocket package marker |

## HTTP API modules (`app/api/v1`)

| File | Responsibility |
| --- | --- |
| `auth.py` | Registration, login, token refresh/revocation, current account |
| `users.py` | User profile and preferred language |
| `astrologers.py` | Astrologer applications, public listing, own profile |
| `astrology.py` | Birth chart request endpoint and language selection |
| `languages.py` | Supported language metadata |
| `locations.py` | Place search endpoint |
| `consultations.py` | Booking, participant-specific listing, status changes |
| `chat.py` | Message history, text/file messages, attachment validation and download |
| `calls.py` | Consultation call start/end records |
| `payments.py` | Payment record creation, listing, and admin status update |
| `reports.py` | AI report request, localized chart/report persistence, sharing and PDF download |
| `reviews.py` | Astrologer review creation and listing |
| `complaints.py` | Complaint creation, listing, and status management |
| `admin.py` | Admin dashboard, astrologer approval, user management |
| `voice.py` | Text-to-speech API endpoint |

## Business services (`app/services`)

| File | Responsibility |
| --- | --- |
| `auth_service.py` | Password hashing, login, registration, token creation |
| `astrology_service.py` | Chart, planetary placements, Rasi/Navamsa, and Dasha/Bhukti calculations |
| `consultation_service.py` | Consultation status transition rules |
| `geocoding_service.py` | External place search and coordinate normalization |
| `report_service.py` | AI provider calls, prompt creation, and branded localized PDF rendering |
| `voice_service.py` | Speech provider integration |
| `__init__.py` | Services package marker |

## Schemas (`app/schemas`)

| File | Responsibility |
| --- | --- |
| `auth.py` | Login, registration, and refresh request models |
| `user.py` | User profile and language preference models |
| `astrology.py` | Birth chart request model |
| `astrologer.py` | Astrologer application/profile models |
| `consultation.py` | Booking and status update models |
| `voice.py` | Speech generation request model |
| `__init__.py` | Schema package marker |

## Persistence models (`app/models`)

| File | Responsibility |
| --- | --- |
| `user.py` | User data model |
| `astrologer.py` | Astrologer profile model |
| `consultation.py` | Consultation model |
| `message.py` | Chat message and attachment model |
| `report.py` | Consultation report model |
| `payment.py` | Payment model |
| `review.py` | Review model |
| `complaint.py` | Complaint model |
| `notification.py` | Notification model |
| `__init__.py` | Shared identifiers, timestamps, and public-document serialization |

## Configuration and shared utilities

| File | Responsibility |
| --- | --- |
| `app/config/settings.py` | Typed environment settings |
| `app/config/database.py` | MongoDB connection and collection access |
| `app/middleware/auth.py` | Current-user dependency and role guards |
| `app/middleware/error_handler.py` | Consistent API error responses |
| `app/utils/security.py` | JWT and password/token security helpers |
| `app/utils/i18n.py` | Supported language codes and chart localization |
| `app/utils/pagination.py` | Pagination helpers |
| `requirements.txt` | Python dependencies |
| `.env.example` | Safe configuration template with blank provider-key values |
