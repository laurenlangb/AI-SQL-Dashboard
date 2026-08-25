# AI Data Analyst App

## Project layout

```
app/
  main.py         FastAPI app, routes, login/logout, dependency-injected auth.
  auth.py         JWT session auth and hardcoded-credential check.
  database.py     SQLite connection (read-only), schema introspection, query execution.
  gemini.py       Question → SQL → answer pipeline using the Gemini API.
  validation.py   sqlglot-based SQL safety validation.
  config.py       Environment variable loading.

static/           Frontend JS and CSS.
templates/        Jinja2 HTML templates (login, dashboard).
tests/            Unit tests (SQL validation + authentication).
example.db        Provided SQLite dataset.
```
## How to run

### Prerequisites
- **Python 3.9 or newer**
- **A Google Gemini API key** 

---
### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd AI-Analyst-application-copy

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file from the template
cp .env.example .env
```

Update the .env file with your actual configuration values.


## Environment variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key, used for NL→SQL generation and answer summarization. | 
| `JWT_SECRET` | Random string used to sign session JWTs. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `DATABASE_PATH` | Path to the SQLite database file. Defaults to `example.db`, but can point to any single-table SQLite file so the app isn't tied to a specific database. |

---
### Run

```bash
uvicorn app.main:app --reload
```

### Log in
Use the demo credentials:

| Field    | Value                            |
| -------- | -------------------------------- |
| Email    | `demo@example.com`               |
| Password | `DemoPassword123!`               |

### Run tests (optional)

```bash
python -m unittest discover
```


---

## Assumptions

- Login requires an exact, case-sensitive match of the email and password 
- The display name ("Example User") is hardcoded
- The database is opened read-only, so neither the user nor a generated query can modify the data
- All columns in the table are stored as `TEXT` (including prices, APRs, mileage, terms, and payments). The AI is instructed to clean and `CAST` them before any math
- The dataset has a single table
- Sessions last 12 hours; logout clears the cookie immediately.
- Each chat question is independent — there is no conversation memory; one question maps to one SQL `SELECT`
- The app is run from the repo root, and the frontend and backend share one origin, so no CORS configuration is needed

---

## Infrastructure writeup
### What technologies and libraries you chose and why.
### How the authentication flow works end-to-end (login → JWT → protected routes).
### How the AI chat pipeline works (user query → SQL generation → execution → response).
I built the application in Python with FastAPI because the project is centered on database access, authentication, and an AI-backed query pipeline. FastAPI provides a lightweight way to define routes for login, protected data access, and chat requests, while Uvicorn runs the app locally. I used Jinja2 templates with plain HTML, CSS, and JavaScript to keep the frontend simple. The app reads from the provided SQLite database using Python’s built-in SQLite support. Environment variables are loaded with `python-dotenv`. I used `google-genai` for Gemini integration and `sqlglot` to parse and validate AI-generated SQL before execution. The tradeoff is that the frontend is less componentized and harder to scale than using the frontend framework, but it keeps the project easier to run.

Authentication uses hardcoded demo credentials. When a user logs in, the backend validates the email and password, creates a signed JWT containing the user’s identity and expiration time, and stores it in an HttpOnly session cookie. Protected pages and API routes check this cookie on each request. If the token is missing, invalid, or expired, the request is rejected or redirected to login. Logging out clears the cookie and returns the user to the login page.

The AI chat pipeline starts when the user submits a question. The backend reads the database schema, sends the schema and question to Gemini, and asks Gemini to produce a SQLite `SELECT` query. Before running the query, the app validates that it is read-only, uses only the expected table and columns, and contains a single safe SELECT statement. If valid, the query runs against the SQLite database, and the result is summarized into a human-readable answer. Invalid, unsafe, or unanswerable questions return a text error instead of crashing or modifying data.  I tested Gemini 2.5 Flash Lite and Gemini 2.5 Flash during development - the difference was not clear enough to determine which was most effective, but if I was continuing this project I would evaluate them more and likely use a stronger model for SQL generation and a cheaper model for answer summarization.

---

## Scale and production design
### If this application were deployed to support hundreds of monthly active users, what architectural changes would you make?
### How would you handle security at scale?
### What observability or monitoring would you add?
If this application were deployed to support hundreds of users, I would first change how the app handles database access and querying. SQLite works well for the local demo dataset, which is small and contains one table. At a larger scale, if many users were running queries at the same time, the dataset grew significantly, the app needed audit logs or user-specific data, or I needed stronger production database monitoring and performance tools, I would move to a production database such as Postgres.

For security, I would keep using environment variables locally, but in production I would store secrets such as the Gemini API key, JWT secret, and database credentials in a managed secrets system. I would also improve token management by using shorter-lived access tokens, refresh tokens if needed, and secret/key rotation. Since this app uses cookies for authentication, I would make sure production cookies are configured with HttpOnly, Secure, and SameSite settings.

I would add rate limiting for both login attempts and chat requests. Login rate limits would help prevent brute-force attempts, while chat rate limits would control Gemini usage and cost. I would also log failed or rejected AI requests, such as unanswerable questions, rate-limit errors, Gemini service errors, and database lookup failures. This would help me understand what users are asking, improve prompts and error handling, and control API cost.

For logging and monitoring, I would replace basic development logs with structured application logs and send them to a production monitoring system such as AWS CloudWatch. The monitoring system could then be used to monitor request volume, error rates, and alert on unusual behavior. For exception tracking, I would also consider a tool like Sentry.

In production, I would run FastAPI behind a more reliable web server setup. This setup would handle HTTPS, and monitor whether the app is healthy. I would package the app with Docker so development, testing, and production environments are consistent. I would also add CI/CD through GitHub Actions to run linting, unit tests, and integration checks before deployment.


---

## AI assistance

I used AI coding agents - Claude Code, to help generate the implementation. The bulk of what I worked on focused on guiding the product direction, architecture, data flow, authentication approach, AI query behavior, testing strategy, and reviewing/debugging the generated code to make sure it was intentional and aligned with the assignment requirements.
