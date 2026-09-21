# Nexus Support — Extended

> An enterprise multi-agent customer support platform: LangGraph supervisor/specialist orchestration, PII scrubbing, and real-time BI analytics.

This project is a modified, extended version of [**Customer-Support-Agent-**](https://github.com/Ismail-2001/Customer-Support-Agent-) ("Nexus Support") by **Ismail Sajid** ([@Ismail-2001](https://github.com/Ismail-2001)), used and redistributed here under the terms of its MIT License. The original author's copyright notice is preserved unmodified in [LICENSE](LICENSE).

**This repository does not claim to be the original creation of its maintainer.** It is a derivative work: the LangGraph supervisor/specialist architecture, the Streamlit UI, and the analytics dashboard are Ismail Sajid's; the items below are additions and fixes made on top of that base.

---

## What This Project Does

A stateful LangGraph agent that routes customer messages to specialist sub-agents (order, tech, billing, general), scrubs PII before it reaches the LLM or the database, escalates to a human when needed, and tracks cost/token telemetry in a live analytics dashboard.

## What Was Changed vs. the Original

### 1. A genuinely working dual-provider LLM fallback
The original's `DualModelProvider` — and its README, which explicitly advertises "a resiliency pattern that can automatically reroute requests to a secondary LLM provider if the primary experiences latency or outages" — was actually `self.secondary = self.primary  # Mocking secondary as the same for this environment`. There was no real fallback. This fork implements one for real: a genuinely independent second provider (OpenAI-compatible, configurable via `FALLBACK_API_KEY`/`FALLBACK_MODEL`/`FALLBACK_API_BASE`), invoked only when the primary call raises. If no fallback key is configured, the provider now says so in the logs and re-raises the original error, rather than silently pretending to have redundancy it doesn't have.

### 2. A real bug fix: the API service never actually started in Docker
Both `Dockerfile`'s `CMD` and `docker-compose.yml` ran `python api.py` — but `api.py` only ever defined the FastAPI `app` object with no `uvicorn.run()` call. Running it directly does nothing and exits; the containerized API never came up. This fork adds a proper `if __name__ == "__main__": uvicorn.run(...)` entry point and fixes the Dockerfile/compose commands and exposed port to match what the README documents (`8001`).

### 3. Removed a hardcoded default secret
`api.py` fell back to `API_KEY = os.getenv("API_KEY", "agentic_secret_key_2026")` — a real default bearer token baked into the source, usable by anyone who read the repo if a deployer forgot to override it. This fork removes the default: the API now refuses to start if `API_KEY` isn't explicitly set.

### 4. Fixed a Windows-breaking database bug
The documented `.env` default, `DATABASE_URL=sqlite:///customers.db`, was passed directly to `sqlite3.connect()`, which doesn't understand SQLAlchemy-style URLs — on Windows this fails outright since `:` isn't a valid filename character. This fork normalizes `sqlite://`/`sqlite:///`-prefixed URLs to a plain path before connecting.

### 5. Expanded PII scrubbing
`_scrub_pii` was documented as covering "Email/Phone/SSN masking" and "Sensitive Identifiers" generally, but the code only masked email and phone. This fork adds SSN masking and Luhn-validated credit card number masking (Luhn-checked specifically so arbitrary long digit strings like order/ticket numbers aren't falsely flagged as card numbers).

### 6. Test suite (`tests/`)
The original had no tests despite listing `pytest` as a dependency. This fork adds 28 tests covering PII scrubbing, the dual-provider fallback logic (including the "no fallback configured" path), the database layer (including the sqlite URL normalization fix), and the individual LangGraph node functions (identify, supervisor routing, order/tech/billing/general specialists, escalation).

---

## Tech Stack

Python, LangGraph, LangChain, DeepSeek (primary LLM) + any OpenAI-compatible provider (fallback, new), Streamlit, FastAPI, SQLite/PostgreSQL, pytest.

## Installation & Setup

```bash
git clone <this-repo-url>
cd nexus-support-extended
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
- `DEEPSEEK_API_KEY` — required
- `FALLBACK_API_KEY` — optional, enables real LLM fallback
- `API_KEY` — required, your own secret for the FastAPI bearer auth (no default is provided)

### Run

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8001
python -m streamlit run app.py
```

Analytics dashboard:

```bash
python -m streamlit run dashboard.py
```

### Docker

```bash
docker compose up --build
```

- API: `http://localhost:8001`
- UI: `http://localhost:8503`

## Testing

```bash
pytest
```

## License

MIT License — see [LICENSE](LICENSE). Original work by Ismail Sajid. Modifications in this repository are made available under the same license.

## Attribution

- **Original project & architecture:** [Ismail Sajid](https://github.com/Ismail-2001) — [Customer-Support-Agent-](https://github.com/Ismail-2001/Customer-Support-Agent-)
- **Extended by:** [Sami123d](https://github.com/Sami123d)
