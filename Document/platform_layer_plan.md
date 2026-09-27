# 🏗️ Platform Layer — Implementation Plan
## VaniSetu Layer 2 | Express + Neon PostgreSQL + React

---

## 👥 Team Structure & Boundaries

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  👤 Developer A — AI Agent Layer (Python)                            │
│     Owns: Telephony, STT/TTS, Conversation AI, NLP                  │
│     Sends data TO our APIs                                           │
│                                                                      │
│  👤 YOU — Platform Layer (Node.js)                           ◄ THIS │
│     Owns: Express backend, Neon DB, APIs, React dashboard            │
│     Provides APIs that everyone consumes                             │
│                                                                      │
│  👤 Developer B — Recommendation Engine + Tracking (Node.js)         │
│     Owns: Skill→NSQF→Training matching algorithm, Follow-up         │
│     scheduler, SMS engine, Outcome tracking                          │
│     Reads from our DB, exposes /recommend endpoint                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### What YOU Build vs What You DON'T

| ✅ You Build | ❌ Others Build |
|-------------|----------------|
| Express server + middleware | Conversation AI engine (Dev A) |
| Neon PostgreSQL + Drizzle schema + migrations | STT/TTS integration (Dev A) |
| All CRUD APIs (beneficiary, programs, enrollment, attendance) | Recommendation algorithm logic (Dev B) |
| Auth (JWT + role-based access) | Follow-up scheduler / cron jobs (Dev B) |
| React admin dashboard (all pages) | SMS micro-survey engine (Dev B) |
| Training Center Portal UI | Outcome collection logic (Dev B) |
| API validation (Zod) | Field worker PWA (Dev B) |

> **Key insight:** You build the **platform** (database + APIs + UI). The other two developers **consume** your APIs and add their logic on top.

---

## 📁 Project Structure

```
vaani/
├── backend/
│   ├── src/
│   │   ├── index.js                    ← Express app entry point
│   │   ├── config/
│   │   │   ├── db.js                   ← Neon + Drizzle connection
│   │   │   └── env.js                  ← Environment variables
│   │   ├── db/
│   │   │   ├── schema.js              ← Drizzle schema (all tables)
│   │   │   ├── seed.js                ← Seed data (NSQF taxonomy, test programs)
│   │   │   └── migrations/            ← Drizzle Kit auto-generated
│   │   ├── routes/
│   │   │   ├── beneficiary.routes.js
│   │   │   ├── program.routes.js
│   │   │   ├── enrollment.routes.js
│   │   │   ├── attendance.routes.js
│   │   │   ├── callLog.routes.js
│   │   │   ├── analytics.routes.js
│   │   │   └── auth.routes.js
│   │   ├── controllers/
│   │   │   ├── beneficiary.controller.js
│   │   │   ├── program.controller.js
│   │   │   ├── enrollment.controller.js
│   │   │   ├── attendance.controller.js
│   │   │   ├── callLog.controller.js
│   │   │   └── analytics.controller.js
│   │   ├── middleware/
│   │   │   ├── auth.js                ← JWT verification + role check
│   │   │   ├── validate.js            ← Zod schema validation middleware
│   │   │   └── errorHandler.js        ← Global error handler
│   │   ├── validators/
│   │   │   ├── beneficiary.validator.js  ← Zod schemas for beneficiary
│   │   │   ├── program.validator.js
│   │   │   └── enrollment.validator.js
│   │   └── utils/
│   │       ├── logger.js
│   │       ├── pagination.js          ← Reusable pagination helper
│   │       └── apiResponse.js         ← Consistent response format
│   ├── package.json
│   ├── drizzle.config.js             ← Drizzle Kit configuration
│   ├── .env                           ← Environment variables (DO NOT commit)
│   └── .env.example                   ← Template for others
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js             ← Axios/fetch wrapper for backend APIs
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BeneficiaryList.jsx
│   │   │   ├── BeneficiaryDetail.jsx
│   │   │   ├── Programs.jsx
│   │   │   ├── TrainingCenterPortal.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── Login.jsx
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Topbar.jsx
│   │   │   │   └── MainLayout.jsx
│   │   │   ├── Cards/
│   │   │   │   └── StatCard.jsx
│   │   │   ├── Tables/
│   │   │   │   └── DataTable.jsx
│   │   │   └── Charts/
│   │   │       ├── FunnelChart.jsx
│   │   │       └── BarChart.jsx
│   │   └── hooks/
│   │       └── useApi.js             ← Custom hook for API calls
│   ├── package.json
│   └── vite.config.js
│
├── docs/                              ← Documentation for other developers
│   ├── INTEGRATION_GUIDE.md          ← How Layer 1 & Dev B connect
│   └── API_REFERENCE.md              ← All endpoints documented
│
├── docker-compose.yml                ← Local dev setup
└── README.md
```

---

## 🔧 Phase 1 — Foundation (Days 1-5)

> **Goal:** Database running, schema deployed, core CRUD APIs working, basic Express server up.

### Day 1: Project Setup

- [ ] Initialize Node.js project: `npm init -y`
- [ ] Install core dependencies (see package list below)
- [ ] Set up Express server with CORS, JSON parser, error handler
- [ ] Create `.env` and `.env.example` with Neon connection string
- [ ] Set up Neon PostgreSQL account + create database
- [ ] Configure Drizzle ORM connection to Neon
- [ ] Test connection: simple query to verify DB works
- [ ] Create `apiResponse.js` utility for consistent response format:
  ```js
  // All APIs return this structure:
  { success: true/false, data: {...}, message: "...", meta: { page, limit, total } }
  ```

### Day 2: Database Schema

- [ ] Write full Drizzle schema (`schema.js`) — all 9 tables
- [ ] Configure `drizzle.config.js` for Drizzle Kit
- [ ] Run `npx drizzle-kit generate` to create migration files
- [ ] Run `npx drizzle-kit push` to deploy schema to Neon
- [ ] Create seed script (`seed.js`):
  - 10 sample NSQF taxonomy entries (Construction, Agriculture, Textiles sectors)
  - 5 sample training programs
  - 3 sample beneficiaries with skills
- [ ] Run seed, verify data in Neon console

### Day 3: Beneficiary APIs

- [ ] Create Zod validators for beneficiary input
- [ ] `POST /api/v1/beneficiary/register` — Create new beneficiary + skills (Layer 1 calls this)
- [ ] `GET /api/v1/beneficiaries` — List all with pagination, filtering (by district, state, status, NSQF level)
- [ ] `GET /api/v1/beneficiary/:id` — Get full profile with skills included
- [ ] `PUT /api/v1/beneficiary/:id` — Update profile
- [ ] `GET /api/v1/beneficiary/:id/skills` — Get skills for a beneficiary
- [ ] `PATCH /api/v1/beneficiary/:id/status` — Update status (used by tracking layer)
- [ ] Test all with Postman/Thunder Client

### Day 4: Training Program APIs + Call Log APIs

- [ ] Create Zod validators for programs
- [ ] `POST /api/v1/programs` — Create training program
- [ ] `GET /api/v1/programs` — List with filters (sector, NSQF level, district, active status)
- [ ] `GET /api/v1/programs/:id` — Get program detail with enrolled count
- [ ] `PUT /api/v1/programs/:id` — Update program
- [ ] `POST /api/v1/programs/bulk-import` — CSV upload to create multiple programs
- [ ] `POST /api/v1/call-logs` — Store call log (Layer 1 sends after each call)
- [ ] `GET /api/v1/call-logs/:beneficiaryId` — Get call history for a beneficiary

### Day 5: Enrollment APIs + Attendance APIs

- [ ] `POST /api/v1/enrollments` — Enroll beneficiary in a program (update enrolled_count)
- [ ] `GET /api/v1/enrollments` — List enrollments (filter by status, program, district)
- [ ] `PATCH /api/v1/enrollments/:id/status` — Update enrollment status
- [ ] `POST /api/v1/attendance` — Mark attendance (training center submits daily)
- [ ] `GET /api/v1/attendance/:enrollmentId` — Get attendance history
- [ ] `GET /api/v1/attendance/batch/:programId` — Get today's batch attendance view
- [ ] Write `.env.example` and update README with setup instructions

**🎯 After Day 5:** Dev A and Dev B can start integrating — the core APIs are live.

---

## 🔧 Phase 2 — Business Logic & Auth (Days 6-9)

> **Goal:** Auth working, role-based access, analytics endpoints, integration-ready.

### Day 6: Authentication & RBAC

- [ ] Install `jsonwebtoken` + `bcryptjs`
- [ ] Create `users` table (or add to schema) for auth:
  ```
  Roles: admin, district_officer, state_officer, training_center, viewer
  ```
- [ ] `POST /api/v1/auth/register` — Create user (admin only)
- [ ] `POST /api/v1/auth/login` — Login, return JWT token
- [ ] Auth middleware: verify JWT, attach `req.user`
- [ ] Role middleware: check if user's role has permission for the route
- [ ] Protect all routes (except `POST /beneficiary/register` — Layer 1 uses API key instead)
- [ ] API key middleware for Layer 1: simple `X-API-Key` header check

### Day 7: Analytics Endpoints

- [ ] `GET /api/v1/analytics/dashboard` — Aggregate stats:
  ```json
  {
    "totalBeneficiaries": 1250,
    "totalSkillsMapped": 2340,
    "totalEnrolled": 890,
    "totalCompleted": 456,
    "totalCertified": 320,
    "avgIncomeChange": 4500,
    "attendanceRate": 87.5,
    "statusBreakdown": { "registered": 200, "enrolled": 400 }
  }
  ```
- [ ] `GET /api/v1/analytics/funnel` — Conversion funnel data
- [ ] `GET /api/v1/analytics/district/:name` — Per-district breakdown
- [ ] `GET /api/v1/analytics/skills-heatmap` — Skill distribution across districts
- [ ] `GET /api/v1/analytics/attendance-summary/:programId` — Batch-level attendance

### Day 8: Integration Endpoints (For Dev B)

These endpoints are consumed by the Recommendation Engine and Tracking modules:

- [ ] `GET /api/v1/recommend/data/:beneficiaryId` — Returns beneficiary skills + location for recommendation engine
- [ ] `POST /api/v1/recommend/result` — Dev B posts recommendation results back
- [ ] `POST /api/v1/followups` — Dev B schedules follow-ups
- [ ] `GET /api/v1/followups/pending` — Dev B's scheduler reads pending items
- [ ] `PATCH /api/v1/followups/:id` — Dev B updates follow-up status after execution
- [ ] `POST /api/v1/outcomes` — Dev B posts outcome data (from AI calls, SMS, field worker)
- [ ] `GET /api/v1/outcomes/:beneficiaryId` — Get outcome history

### Day 9: API Documentation + Error Handling Polish

- [ ] Add request logging middleware (morgan)
- [ ] Improve error messages for all validation failures
- [ ] Add rate limiting for public endpoints
- [ ] Write API_REFERENCE.md with all endpoints, request/response examples
- [ ] Write INTEGRATION_GUIDE.md for Dev A and Dev B
- [ ] Set up CORS whitelist for frontend domain

---

## 🔧 Phase 3 — Frontend Dashboard (Days 10-14)

> **Goal:** React dashboard with all core pages functional.

### Day 10: React Project + Layout

- [ ] `npm create vite@latest frontend -- --template react`
- [ ] Install: `react-router-dom`, `axios`, `recharts`, `react-icons`, `react-hot-toast`
- [ ] Create `MainLayout` with Sidebar + Topbar
- [ ] Set up React Router with all page routes
- [ ] Create `api/client.js` — Axios instance with base URL + JWT token header
- [ ] Create `useApi` custom hook for loading/error states

### Day 11: Dashboard Home + Login

- [ ] Login page: email + password form → JWT stored in localStorage
- [ ] Dashboard page: Stat cards (total beneficiaries, enrolled, completed, attendance rate)
- [ ] Status breakdown bar chart
- [ ] Recent registrations list (last 10)
- [ ] Quick action buttons (Add Program, View All Beneficiaries)

### Day 12: Beneficiary Pages

- [ ] Beneficiary List page: searchable table, filters, pagination, click → detail
- [ ] Beneficiary Detail page: personal info, skills with NSQF badges, training history, call logs, outcomes

### Day 13: Programs + Training Center Portal

- [ ] Programs list page: table with filters (sector, NSQF, district)
- [ ] Add/Edit program form
- [ ] Training Center Portal page (separate role login):
  - Select batch/program → checkbox list → mark attendance → submit
  - View batch attendance summary + at-risk students highlighted

### Day 14: Analytics + Polish

- [ ] Analytics page: conversion funnel, district-wise charts, skill distribution, attendance trends
- [ ] Responsive design check (tablet + mobile)
- [ ] Loading skeletons, toast notifications, final testing

---

## 📦 NPM Packages

### Backend

```json
{
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.0",
    "@neondatabase/serverless": "^0.9.0",
    "drizzle-orm": "^0.30.0",
    "zod": "^3.22.0",
    "jsonwebtoken": "^9.0.0",
    "bcryptjs": "^2.4.3",
    "morgan": "^1.10.0",
    "multer": "^1.4.5",
    "csv-parser": "^3.0.0",
    "express-rate-limit": "^7.1.0"
  },
  "devDependencies": {
    "drizzle-kit": "^0.21.0",
    "nodemon": "^3.0.0"
  }
}
```

### Frontend

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0",
    "react-icons": "^4.12.0",
    "react-hot-toast": "^2.4.0",
    "dayjs": "^1.11.0"
  }
}
```

---

## 🔑 Environment Variables

```env
# .env.example

# Neon PostgreSQL
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/vanisetu?sslmode=require

# Server
PORT=3001
NODE_ENV=development

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_EXPIRES_IN=7d

# API Key (for Layer 1 to call our APIs)
LAYER1_API_KEY=vanisetu-layer1-secret-key-2025

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

---

## 📐 API Response Format (ALL endpoints)

```js
// ✅ Success
{
  "success": true,
  "data": { ... },
  "message": "Beneficiary registered successfully",
  "meta": { "page": 1, "limit": 20, "total": 156, "totalPages": 8 }
}

// ❌ Error
{
  "success": false,
  "data": null,
  "message": "Validation failed",
  "errors": [{ "field": "phone", "message": "Phone number is required" }]
}
```

---

## ⚠️ Phase Dependencies

```
Phase 1 (Foundation)         Phase 2 (Business Logic)       Phase 3 (Frontend)
━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━
DB Schema ──────────────┐
Express Server ─────────┤
Beneficiary APIs ───────┼──► Auth & RBAC ──────────────┐
Program APIs ───────────┤    Analytics APIs ────────────┼──► Dashboard ──────►
Enrollment APIs ────────┤    Integration Endpoints ─────┤    Beneficiary Pages
Attendance APIs ────────┘    API Documentation ─────────┘    Programs Page
                                                             Training Center
                                                             Analytics Page

🔴 Phase 1 blocks Phase 2    🟡 Phase 2 blocks Phase 3
   (need DB + APIs first)       (need auth + analytics)
```

> **Dev A and Dev B can start integrating as soon as Phase 1 Day 3 is done.**
