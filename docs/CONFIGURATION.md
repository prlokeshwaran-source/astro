# Backend Configuration

Settings are loaded from environment variables and `.env` using Pydantic Settings. `.env.example` lists the supported names. Restart Uvicorn after changing `.env`.

| Variable | Required | Purpose |
| --- | --- | --- |
| `MONGODB_URI` | Yes | MongoDB connection URI |
| `MONGODB_DB` | No | Database name; defaults to `astrology_platform` |
| `JWT_SECRET` | Yes | Secret used to sign access and refresh tokens |
| `JWT_ALGORITHM` | No | JWT algorithm; defaults to `HS256` |
| `ACCESS_TOKEN_MINUTES` | No | Access token lifetime |
| `REFRESH_TOKEN_DAYS` | No | Refresh token lifetime |
| `CORS_ORIGINS` | No | Comma-separated allowed browser origins |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | No | Bootstrap first admin when that email is not already registered |
| `AI_PROVIDER` | No | `gemini` by default, or `openai` |
| `GEMINI_API_KEY` | For Gemini | Google AI Studio key |
| `GEMINI_MODEL` | No | Gemini model name |
| `OPENAI_API_KEY` | For OpenAI | OpenAI API key |
| `REPORT_AI_MODEL` | No | OpenAI report model |
| `TTS_MODEL` | No | Text-to-speech model |
| `GEOCODER_USER_AGENT` | No | User agent for geocoding requests |

## Example development setup

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=astrology_platform
JWT_SECRET=replace-with-a-long-random-value
CORS_ORIGINS=http://localhost:5173
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-unique-password
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-flash-lite
```

Keep real credentials in an ignored `.env` file or a deployment secret store. Never put backend provider keys in the frontend's `VITE_` environment variables. The admin bootstrap is creation-only; it does not update the password for an existing account.

## Tamil and Hindi PDF support

Install dependencies with `pip install -r requirements.txt` to include ReportLab and `uharfbuzz`. The renderer searches Windows Nirmala UI and common Linux Noto Sans paths. On Linux, install Noto Sans Tamil and Devanagari fonts if the distribution does not already provide them. The font must contain the selected script's glyphs.
