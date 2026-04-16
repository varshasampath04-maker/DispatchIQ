# DispatchIQ — Logistics AI Dispatch Agent

> Real-time driver monitoring, risk scoring, and customer notification — powered by event-driven AI.

---

## What It Does

DispatchIQ monitors all drivers with deliveries today. It categorizes each driver by status, scores risk using GPS + transcript NLP, and lets managers control everything from one dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Queue | RabbitMQ |
| Workers | 2x Python worker instances (parallel) |
| AI Layer | Groq API (Tamil/Hindi NLP scoring) |
| Auth | JWT + OTP via email (SMTP) |
| Infra | Docker + docker-compose |

---

## Architecture

```
Frontend → POST /dispatch (JWT)
         ↓
      FastAPI
   → validate JWT + role
   → categorize drivers (DB only)
   → push 1 job per driver → RabbitMQ
         ↓
  Worker1 ──┐
            ├── parallel atomic pickup
  Worker2 ──┘
         ↓
   engine.py
   → GPS anomaly + transcript NLP + time signals
   → risk_score + decision
         ↓
      PostgreSQL updated
         ↓
   Frontend polls → RAG table
```

---

## Driver Status Categories

| Status | Condition |
|---|---|
| `NOT_STARTED` | trip not started AND current time > ETA - 1hr |
| `LATE` | trip started AND past ETA AND not delivered |
| `UNCONFIRMED` | trip started AND within ETA window AND GPS silent > 30min |
| `DELIVERED` | delivered = true |

---

## Risk Engine Signals

```python
score += 0.3   # if LATE
score += 0.4   # if NOT_STARTED
score += 0.2   # if GPS dark > 30min
score += groq_result.uncertainty_level * 0.3  # transcript NLP
score += 0.2   # if contradiction detected

# Decision
score >= 0.7 → ESCALATE
score >= 0.4 → MONITOR
else         → RESOLVE
```

---

## Project Structure

```
dispatchiq/
├── docker-compose.yml
├── .env
├── frontend/
│   └── (React app)
└── backend/
    ├── main.py          # FastAPI routes
    ├── auth.py          # OTP + JWT
    ├── rbac.py          # role middleware
    ├── engine.py        # risk scoring + Groq NLP
    ├── worker.py        # RabbitMQ consumer
    ├── database.py      # PostgreSQL + PII encryption + mock seed
    ├── models.py        # Pydantic schemas
    ├── requirements.txt
    └── Dockerfile
```

---

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- RabbitMQ
- Node.js 18+ (frontend)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/dispatchiq.git
cd dispatchiq/backend
```

Create `.env` in `backend/`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dispatchiq
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
JWT_SECRET=your_secret_key
GROQ_API_KEY=your_groq_api_key
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 2. Database

```bash
psql -U postgres -c "CREATE DATABASE dispatchiq;"
pip install -r requirements.txt
python database.py   # creates tables + seeds 8 mock drivers
```

### 3. Run (3 terminals)

```bash
# Terminal 1 — API
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Worker 1
cd backend && set WORKER_ID=worker1 && python worker.py

# Terminal 3 — Worker 2
cd backend && set WORKER_ID=worker2 && python worker.py
```

### 4. Docker (alternative)

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/send-otp` | None | Send OTP to email |
| POST | `/auth/verify-otp` | None | Verify OTP → get JWT |
| POST | `/dispatch` | JWT (manager) | Trigger dispatch for all today's drivers |
| GET | `/shipments` | JWT | Get all shipments with status |
| GET | `/shipments/{id}` | JWT | Drill down — single driver detail |
| GET | `/logs` | JWT (admin) | Execution trace logs |

---

## Auth Flow

```
1. POST /auth/send-otp  {email}
   → 6-digit OTP sent to email (5min expiry)

2. POST /auth/verify-otp  {email, otp}
   → returns JWT token

3. All protected routes require:
   Authorization: Bearer <token>
```

---

## RBAC

| Role | Permissions |
|---|---|
| `manager` | view dashboard, run dispatch, see all drivers |
| `admin` | manage users, view logs, change settings |

---

## PII Protection

- `driver_phone`, `customer_phone`, `driver_email` — Fernet encrypted in DB
- Frontend never receives raw phone numbers
- API returns masked format: `+91 98*** ***44`

---

## Mock Drivers (Demo Data)

| ID | Driver | Status | Transcript |
|---|---|---|---|
| SH-101 | Ravi | LATE | "traffic la irukken" |
| SH-102 | Arjun | NOT_STARTED | — |
| SH-103 | Priya | DELIVERED | "delivered sir" |
| SH-104 | Suresh | UNCONFIRMED | "almost there" |
| SH-105 | Kumar | DELIVERED | "customer sign panni tattan" |
| SH-106 | Meena | LATE | "vehicle problem" |
| SH-107 | Vijay | UNCONFIRMED | — |
| SH-108 | Divya | LATE | "almost reached" |

---

## Demo Flow

1. Login → OTP arrives live in email
2. JWT stored → dashboard loads
3. Click **"Check all drivers today"**
4. Trace panel: `8 jobs pushed to RabbitMQ`
5. `Worker1 picked SH-101, Worker2 picked SH-102` (parallel)
6. Dashboard populates with RAG colors
7. Click Ravi → LATE + GPS dark + Tamil transcript → risk 0.82 → **ESCALATE**
8. Hit `/dispatch` without token → `403 Forbidden`

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `RABBITMQ_URL` | RabbitMQ AMQP URL |
| `JWT_SECRET` | Secret key for JWT signing |
| `GROQ_API_KEY` | Groq API key for NLP scoring |
| `SMTP_EMAIL` | Gmail address for OTP |
| `SMTP_PASSWORD` | Gmail app password |

---

## License

MIT

