# Astrology Consultation Backend

FastAPI and MongoDB backend for the Astra astrology consultation application. It serves authenticated user, astrologer, and admin workflows, chart calculations, consultation chat, report generation, and supporting services.

## Requirements

- Python 3.11 or newer
- MongoDB, local or hosted
- A Gemini API key for Gemini report generation (or an OpenAI key when configured for OpenAI)
- HarfBuzz support for properly shaped Tamil and Hindi PDF text (`uharfbuzz` is installed from `requirements.txt`)
- A Unicode font with the required script glyphs. On Windows the PDF renderer checks Nirmala UI; on Linux it checks common Noto Sans locations.

## Setup

Run these commands in PowerShell from the backend directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set at least:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=astrology_platform
JWT_SECRET=<long-random-secret>
CORS_ORIGINS=http://localhost:5173
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=<long-unique-password>
AI_PROVIDER=gemini
GEMINI_API_KEY=<your-key>
```

Keep `.env` private and do not commit credentials. The configured admin is created during application startup only when its email is not already registered. Changing `ADMIN_PASSWORD` later does not reset an existing account password.

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is at `/docs`, health status at `/health`, and versioned routes are under `/api/v1`.

## AI reports

Gemini is the default provider. Configure `GEMINI_API_KEY` and optionally `GEMINI_MODEL`. For OpenAI, set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `REPORT_AI_MODEL`. Report language is selected per request and supported values are `en`, `ta`, and `hi`. Generated PDF documents store the chosen language and use a branded Astra layout.

## Main endpoints

| Area | Routes |
| --- | --- |
| Authentication | `/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/me` |
| User profile and language | `/api/v1/users/me`, `/api/v1/users/me/language` |
| Astrologers | `/api/v1/astrologers` and `/api/v1/astrologers/me` |
| Astrology and locations | `/api/v1/astrology/chart`, `/api/v1/locations/search`, `/api/v1/languages` |
| Consultations | `/api/v1/consultations` |
| Chat and attachments | `/api/v1/chat/{consultation_id}/messages` |
| Live chat | `/ws/chat/{consultation_id}` |
| Calls and payments | `/api/v1/calls`, `/api/v1/payments` |
| Reports | `/api/v1/reports`, `/api/v1/reports/generate` |
| Reviews and complaints | `/api/v1/reviews`, `/api/v1/complaints` |
| Administration | `/api/v1/admin` |

See [docs/API.md](docs/API.md) for route and access details, [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for environment variables, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for request/data flow, and [docs/FILE_GUIDE.md](docs/FILE_GUIDE.md) for a file-by-file source map.

## Architecture

`app/main.py` creates the FastAPI application and database lifecycle. `app/api/router.py` mounts versioned endpoints. API modules validate requests and enforce role access; business logic is kept in `app/services`. MongoDB collections are accessed through the shared database client in `app/config/database.py`.
