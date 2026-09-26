# 🔄 MVP Breakdown — Updates & Answers

---

## 🎯 Question 1: Hybrid Tracking (Layer 3)

You're absolutely right — **we can't just call the beneficiary and ask "how's training going?"** for every stage. Here's why, and the hybrid approach:

### ❌ Why Voice-Only Tracking Fails

```
Stage: ENROLLED → ATTENDING → COMPLETED → CERTIFIED → EMPLOYED

Problems with just calling:
━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ "Are you attending training?"     → Beneficiary can LIE (says yes, but isn't going)
❌ "Did you complete training?"      → We need PROOF, not self-reporting
❌ "Did you get certificate?"        → Certificate is issued by training center, NOT beneficiary
❌ "Did you get a job?"              → Beneficiary might not pick up the call 3 months later
❌ Calling 10,000+ people monthly    → Not scalable even for AI
```

### ✅ The Hybrid Approach — 5 Data Sources

The key insight: **different stages need different data sources**. Not everything comes from the beneficiary.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     HYBRID TRACKING SYSTEM                              │
│                                                                         │
│   SOURCE 1          SOURCE 2          SOURCE 3         SOURCE 4         │
│   ─────────         ─────────         ─────────        ─────────        │
│   🏫 Training       📱 SMS Micro-     📞 AI Voice      👤 Field         │
│   Center Portal     Surveys           Follow-ups       Worker App       │
│                                                                         │
│   Training center   Simple YES/NO     Deeper           Spot-checks      │
│   staff marks       SMS replies       conversations    & verification   │
│   attendance,       from beneficiary  for qualitative  by govt field    │
│   completion,       (no smartphone    data (income,    staff            │
│   grades, certs     needed)           satisfaction)                     │
│                                                                         │
│                          SOURCE 5                                       │
│                          ─────────                                      │
│                          🔗 Govt System                                 │
│                          Integration                                    │
│                                                                         │
│                          PM-AJAY Portal                                 │
│                          API / bulk data                                │
│                          sync for cert                                  │
│                          verification                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 📊 Data Source Matrix — WHO provides WHAT at EACH stage

| Lifecycle Stage | Primary Data Source | What Data | Secondary Source |
|----------------|-------------------|-----------|-----------------|
| **REGISTERED** | 📞 AI Voice Call (Layer 1) | Name, skills, location, income | — |
| **ASSESSED** | 🧠 AI Engine (Auto) | NSQF level, training match | — |
| **ENROLLED** | 🏫 Training Center Portal | "Yes, Ramesh is enrolled in batch #12" | 📱 SMS to beneficiary confirming |
| **ATTENDING** | 🏫 Training Center Portal | Daily attendance (mark present/absent) | 👤 Field worker spot-check |
| **DROPPED** | 🏫 Training Center Portal | "Ramesh absent 5+ days" → auto-flag | 📞 AI calls to ask why + convince to return |
| **COMPLETED** | 🏫 Training Center Portal | "Ramesh completed training, scored 78%" | — |
| **CERTIFIED** | 🔗 Govt System / Training Center | Certificate ID, NSQF level, date | 🏫 Training center uploads cert |
| **EMPLOYED** | 📞 AI Voice Follow-up + 📱 SMS | "Got job at furniture shop, earning ₹12K/month" | 👤 Field worker verification (sample) |

### 🏫 Source 1: Training Center Portal (Most Important!)

This is a **simple web form** that training center staff fill daily. No fancy tech needed.

```
TRAINING CENTER DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━

Login: training_center_ranchi_01 / password

┌─────────────────────────────────────────────────────┐
│  📋 Today's Attendance — Batch: Advanced Carpentry  │
│  Date: 2025-10-15                                   │
│                                                     │
│  ☑ Ramesh Kumar        — Present                   │
│  ☑ Sunil Paswan        — Present                   │
│  ☐ Meena Devi          — Absent                    │
│  ☑ Ajay Bharti         — Present                   │
│                                                     │
│  [Submit Attendance]                                │
│                                                     │
│  📊 Batch Progress: Day 22 of 90                   │
│  👥 Attendance Rate: 87%                           │
│  ⚠️ At-risk: Meena Devi (absent 4 days)           │
└─────────────────────────────────────────────────────┘
```

**Key actions for training center staff:**
- Mark daily attendance (checkbox list)
- Record assessment scores
- Upload completion certificates
- Flag dropouts
- Report any issues

### 📱 Source 2: SMS Micro-Surveys (For Beneficiary)

These are **dead-simple SMS messages** that need only a **1-digit reply**. Works on ANY phone.

```
Example SMS flows:
━━━━━━━━━━━━━━━━━

TRAINING START CONFIRMATION:
→ "Ramesh ji, aapki carpentry training kal se hai.
   Kya aap aa rahe hain? Reply: 1=Haan, 2=Nahi"
← Reply: 1
✅ Status: Confirmed

MID-TRAINING CHECK:
→ "Training kaisi chal rahi hai?
   Reply: 1=Bahut acchi, 2=Theek, 3=Problem hai"
← Reply: 3
🚨 Alert → District officer notified → AI calls beneficiary to understand

POST-TRAINING INCOME CHECK (30 days later):
→ "Kya aapki income badhi hai training ke baad?
   Reply: 1=Haan, 2=Nahi, 3=Wahi hai"
← Reply: 1
→ "Kitni badhi? Reply: 1=Thodi, 2=Double, 3=Bahut zyada"
← Reply: 2
✅ Outcome recorded: income doubled
```

### 📞 Source 3: AI Voice Follow-up (Selective, Not Everyone)

AI calls are **expensive** (compute + telephony cost). Use them **selectively**:

| When to Use AI Calls | When NOT to Use |
|----------------------|----------------|
| ✅ Post-training outcome survey (needs detailed conversation) | ❌ Daily attendance (training center does this) |
| ✅ Dropout investigation (why did they leave?) | ❌ Simple yes/no checks (SMS is enough) |
| ✅ 90-day / 180-day impact assessment | ❌ Certificate confirmation (system data) |
| ✅ Beneficiary who didn't respond to SMS 2x | ❌ Routine reminders (SMS cheaper) |

### 👤 Source 4: Field Worker App (Sample Verification)

Government field workers do **sample spot-checks** (not everyone, maybe 10% random sample):

```
FIELD WORKER MOBILE APP (Simple PWA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Visit: Ramesh Kumar, Bara Ghaghra village

Checklist:
☑ Verified: Beneficiary exists at this address
☑ Verified: Attending training at ABC center
☑ Photo: Training center attendance register
☐ Verified: Using new skills for livelihood

📝 Notes: "Ramesh is attending regularly. Making
furniture on weekends using new techniques."

[Submit with GPS + Timestamp]
```

### 🔄 How It All Fits Together

```
                    BENEFICIARY
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    📞 AI Voice    📱 SMS Reply   (Passive)
    (registration,  (quick checks,  (doesn't
     follow-ups)    confirmations)   need to
                                     do anything)
                                        │
                                        ▼
                              🏫 Training Center
                              (attendance, scores,
                               certificates)
                                        │
                                        ▼
                              📊 TRACKING DATABASE
                              (all sources merge here)
                                  │         │
                                  ▼         ▼
                          👤 Field Worker  🔗 Govt System
                          (spot-checks)   (cert verification)
                                  │         │
                                  ▼         ▼
                              📊 ANALYTICS DASHBOARD
                              (district officers see
                               unified view)
```

---

## 🎯 Question 2: Tech Stack → Node.js + Express + Neon Postgres

Updated tech stack for the entire project:

### Updated Stack

| Component | Old | **New** | Why |
|-----------|-----|---------|-----|
| Backend | Python FastAPI | **Node.js + Express** | Team preference, JS everywhere |
| Database | PostgreSQL (self-hosted) | **Neon PostgreSQL** (serverless) | Auto-scaling, no infra management, free tier |
| ORM | SQLAlchemy | **Drizzle ORM** | Type-safe, great DX, SQL-like syntax, works great with Neon |
| Task Queue | Celery + Redis | **BullMQ + Redis** (or **node-cron** for simple scheduling) | Node.js native |
| SMS | MSG91 / Twilio | **Same** (MSG91 / Twilio) | Both have Node.js SDKs |
| Validation | Pydantic | **Zod** | Runtime validation for Node.js, pairs with Drizzle |
| Auth | JWT (Python) | **jsonwebtoken + bcrypt** | Standard Node.js JWT auth |

### Updated Project Structure

```
vaani/
├── layer-1-ai-agent/          ← Person A + B (can stay Python — AI/ML is better in Python)
│   ├── telephony/
│   │   ├── exotel_handler.py
│   │   └── call_state_machine.py
│   ├── stt_tts/
│   │   ├── bhashini_client.py
│   │   └── whisper_fallback.py
│   ├── conversation/
│   │   ├── agent.py
│   │   ├── prompts/
│   │   │   ├── greeting.txt
│   │   │   ├── skill_extraction.txt
│   │   │   └── recommendation.txt
│   │   └── entity_extractor.py
│   ├── nsqf/
│   │   ├── mapper.py
│   │   └── taxonomy.json
│   ├── requirements.txt
│   └── Dockerfile
│
├── layer-2-platform/          ← Person C + D (Node.js + Express)
│   ├── backend/
│   │   ├── src/
│   │   │   ├── index.js               ← Express app entry
│   │   │   ├── config/
│   │   │   │   ├── db.js              ← Neon connection (Drizzle)
│   │   │   │   └── env.js             ← Environment variables
│   │   │   ├── db/
│   │   │   │   ├── schema.js          ← Drizzle schema definitions
│   │   │   │   └── migrations/        ← Drizzle migration files
│   │   │   ├── routes/
│   │   │   │   ├── beneficiary.routes.js
│   │   │   │   ├── program.routes.js
│   │   │   │   ├── enrollment.routes.js
│   │   │   │   ├── analytics.routes.js
│   │   │   │   └── auth.routes.js
│   │   │   ├── controllers/
│   │   │   │   ├── beneficiary.controller.js
│   │   │   │   ├── program.controller.js
│   │   │   │   ├── enrollment.controller.js
│   │   │   │   └── analytics.controller.js
│   │   │   ├── middleware/
│   │   │   │   ├── auth.js             ← JWT verification
│   │   │   │   ├── validate.js         ← Zod validation middleware
│   │   │   │   └── errorHandler.js
│   │   │   ├── services/
│   │   │   │   ├── recommendation.service.js  ← Matching engine
│   │   │   │   ├── sms.service.js             ← MSG91/Twilio
│   │   │   │   └── followup.service.js
│   │   │   └── utils/
│   │   │       ├── logger.js
│   │   │       └── helpers.js
│   │   ├── package.json
│   │   ├── drizzle.config.js
│   │   └── Dockerfile
│   │
│   └── frontend/              ← React dashboard
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   └── ...
│       └── package.json
│
├── layer-3-tracking/          ← Person E + F (Node.js)
│   ├── src/
│   │   ├── scheduler/
│   │   │   ├── cron.js                ← node-cron jobs
│   │   │   └── followup.worker.js     ← BullMQ worker
│   │   ├── sms/
│   │   │   ├── templates.js           ← SMS message templates
│   │   │   └── micro-survey.js        ← SMS survey handler
│   │   └── analytics/
│   │       └── aggregator.js          ← Compute KPIs from DB
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

> [!IMPORTANT]
> **Layer 1 can stay in Python** even though backend is Node.js — they communicate via REST APIs. AI/ML libraries (Bhashini SDK, Whisper, spaCy, LLM clients) are much more mature in Python. The two layers are separate services connected by HTTP.

### Neon PostgreSQL Connection (Drizzle ORM)

```js
// backend/src/config/db.js
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from '../db/schema.js';

const sql = neon(process.env.DATABASE_URL);
export const db = drizzle(sql, { schema });
```

### Drizzle Schema (Replaces SQLAlchemy)

```js
// backend/src/db/schema.js
import { pgTable, uuid, varchar, integer, boolean,
         timestamp, text, real, date, pgEnum } from 'drizzle-orm/pg-core';

// ── Enums ──
export const statusEnum = pgEnum('status', [
  'registered', 'assessed', 'enrolled', 
  'attending', 'dropped', 'completed', 
  'certified', 'employed'
]);

export const enrollmentStatusEnum = pgEnum('enrollment_status', [
  'enrolled', 'attending', 'completed', 'dropped', 'certified'
]);

// ── Beneficiaries ──
export const beneficiaries = pgTable('beneficiaries', {
  id:              uuid('id').primaryKey().defaultRandom(),
  phone:           varchar('phone', { length: 15 }).unique().notNull(),
  name:            varchar('name', { length: 100 }).notNull(),
  age:             integer('age'),
  gender:          varchar('gender', { length: 10 }),
  district:        varchar('district', { length: 100 }),
  state:           varchar('state', { length: 100 }),
  village:         varchar('village', { length: 200 }),
  casteCategory:   varchar('caste_category', { length: 10 }).default('SC'),
  educationLevel:  varchar('education_level', { length: 50 }),
  monthlyIncome:   integer('monthly_income'),
  householdSize:   integer('household_size'),
  bplStatus:       boolean('bpl_status').default(true),
  language:        varchar('language', { length: 10 }),
  status:          statusEnum('status').default('registered'),
  createdAt:       timestamp('created_at').defaultNow(),
  updatedAt:       timestamp('updated_at').defaultNow(),
});

// ── Skills ──
export const beneficiarySkills = pgTable('beneficiary_skills', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id),
  skillName:       varchar('skill_name', { length: 200 }).notNull(),
  sector:          varchar('sector', { length: 100 }),
  subSector:       varchar('sub_sector', { length: 100 }),
  experienceYears: integer('experience_years'),
  isPrimary:       boolean('is_primary').default(false),
  nsqfLevel:       integer('nsqf_level'),
  confidenceScore: real('confidence_score'),
  subSkills:       text('sub_skills').array(),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── Training Programs ──
export const trainingPrograms = pgTable('training_programs', {
  id:              uuid('id').primaryKey().defaultRandom(),
  name:            varchar('name', { length: 200 }).notNull(),
  sector:          varchar('sector', { length: 100 }),
  subSector:       varchar('sub_sector', { length: 100 }),
  nsqfLevel:       integer('nsqf_level'),
  durationDays:    integer('duration_days'),
  district:        varchar('district', { length: 100 }),
  state:           varchar('state', { length: 100 }),
  trainingCenter:  varchar('training_center', { length: 200 }),
  provider:        varchar('provider', { length: 200 }),
  capacity:        integer('capacity'),
  enrolledCount:   integer('enrolled_count').default(0),
  startDate:       date('start_date'),
  endDate:         date('end_date'),
  isActive:        boolean('is_active').default(true),
  certification:   varchar('certification', { length: 100 }),
  scheme:          varchar('scheme', { length: 100 }).default('PM-AJAY GIA'),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── Enrollments ──
export const enrollments = pgTable('enrollments', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id),
  programId:       uuid('program_id').references(() => trainingPrograms.id),
  status:          enrollmentStatusEnum('status').default('enrolled'),
  enrolledAt:      timestamp('enrolled_at').defaultNow(),
  startedAt:       timestamp('started_at'),
  completedAt:     timestamp('completed_at'),
  certificateId:   varchar('certificate_id', { length: 100 }),
  matchScore:      real('match_score'),
});

// ── Call Logs ──
export const callLogs = pgTable('call_logs', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id),
  callId:          varchar('call_id', { length: 100 }).unique(),
  callType:        varchar('call_type', { length: 20 }),
  durationSeconds: integer('duration_seconds'),
  language:        varchar('language', { length: 10 }),
  transcript:      text('transcript'),
  aiConfidence:    real('ai_confidence'),
  rawAudioUrl:     varchar('raw_audio_url', { length: 500 }),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── Follow-ups ──
export const followups = pgTable('followups', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id),
  followupType:    varchar('followup_type', { length: 20 }),  // sms, call, whatsapp
  scheduledAt:     timestamp('scheduled_at').notNull(),
  executedAt:      timestamp('executed_at'),
  status:          varchar('status', { length: 20 }).default('pending'),
  purpose:         varchar('purpose', { length: 200 }),
  responseSummary: text('response_summary'),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── Outcomes ──
export const outcomes = pgTable('outcomes', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id),
  enrollmentId:    uuid('enrollment_id').references(() => enrollments.id),
  checkDate:       date('check_date'),
  incomeBefore:    integer('income_before'),
  incomeAfter:     integer('income_after'),
  employmentStatus: varchar('employment_status', { length: 50 }),
  isUsingSkill:    boolean('is_using_skill'),
  satisfaction:    integer('satisfaction'),
  notes:           text('notes'),
  dataSource:      varchar('data_source', { length: 20 }),  // 'ai_call', 'sms', 'field_worker'
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── Attendance (NEW — Training center fills this) ──
export const attendance = pgTable('attendance', {
  id:              uuid('id').primaryKey().defaultRandom(),
  enrollmentId:    uuid('enrollment_id').references(() => enrollments.id),
  date:            date('date').notNull(),
  isPresent:       boolean('is_present').default(false),
  markedBy:        varchar('marked_by', { length: 100 }),  // training center staff username
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── NSQF Taxonomy (reference/seed data) ──
export const nsqfTaxonomy = pgTable('nsqf_taxonomy', {
  id:              uuid('id').primaryKey().defaultRandom(),
  sector:          varchar('sector', { length: 100 }).notNull(),
  subSector:       varchar('sub_sector', { length: 100 }),
  skillName:       varchar('skill_name', { length: 200 }).notNull(),
  nsqfLevel:       integer('nsqf_level'),
  qualificationPack: varchar('qualification_pack', { length: 100 }),
  description:     text('description'),
  keywords:        text('keywords').array(),
});
```

### Express Server Setup

```js
// backend/src/index.js
import express from 'express';
import cors from 'cors';
import { config } from './config/env.js';
import beneficiaryRoutes from './routes/beneficiary.routes.js';
import programRoutes from './routes/program.routes.js';
import enrollmentRoutes from './routes/enrollment.routes.js';
import analyticsRoutes from './routes/analytics.routes.js';
import authRoutes from './routes/auth.routes.js';
import { errorHandler } from './middleware/errorHandler.js';

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.use('/api/v1/beneficiary', beneficiaryRoutes);
app.use('/api/v1/programs', programRoutes);
app.use('/api/v1/enrollments', enrollmentRoutes);
app.use('/api/v1/analytics', analyticsRoutes);
app.use('/api/v1/auth', authRoutes);

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// Error handler
app.use(errorHandler);

app.listen(config.PORT, () => {
  console.log(`VaniSetu API running on port ${config.PORT}`);
});
```

### Updated Task Scheduling (Node.js)

```js
// layer-3-tracking/src/scheduler/cron.js
import cron from 'node-cron';
import { db } from '../../layer-2-platform/backend/src/config/db.js';
import { followups } from '../../layer-2-platform/backend/src/db/schema.js';
import { sendSMS } from '../sms/templates.js';
import { eq, lte, and } from 'drizzle-orm';

// Run every 15 minutes — check for pending follow-ups
cron.schedule('*/15 * * * *', async () => {
  const now = new Date();
  
  const pendingFollowups = await db
    .select()
    .from(followups)
    .where(
      and(
        eq(followups.status, 'pending'),
        lte(followups.scheduledAt, now)
      )
    );

  for (const fu of pendingFollowups) {
    if (fu.followupType === 'sms') {
      await sendSMS(fu.beneficiaryId, fu.purpose);
    } else if (fu.followupType === 'call') {
      // Trigger Layer 1 outbound call API
      await fetch('http://layer1:5000/api/outbound-call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          beneficiary_id: fu.beneficiaryId,
          purpose: fu.purpose
        })
      });
    }

    // Mark as executed
    await db
      .update(followups)
      .set({ status: 'sent', executedAt: now })
      .where(eq(followups.id, fu.id));
  }
  
  console.log(`Processed ${pendingFollowups.length} follow-ups`);
});
```

---

## 📋 Updated Layer 3 Task Breakdown (Hybrid)

### 👤 Person E — Tracking & Hybrid Data Collection

| # | Task | Description | Priority |
|---|------|-------------|----------|
| E1 | **Training Center Portal** | Simple web form: login, mark attendance, record scores, upload certs. React page in the admin dashboard | 🔴 P0 |
| E2 | **Attendance API** | `POST /api/v1/attendance` — training center marks daily attendance per batch | 🔴 P0 |
| E3 | **Auto Dropout Detection** | Cron job: if beneficiary absent 5+ consecutive days → status = 'at_risk' → alert district officer + trigger AI follow-up call | 🔴 P0 |
| E4 | **SMS Micro-Survey Engine** | Send template SMS, parse numeric replies (1/2/3), update DB. Using MSG91 2-way SMS | 🟡 P1 |
| E5 | **Follow-up Scheduler** | node-cron checks `followups` table every 15 min, executes pending SMS/calls | 🔴 P0 |
| E6 | **Outcome Collection** | Multi-source: AI call data (from Layer 1) + SMS survey data + field worker data → merged into `outcomes` table | 🟡 P1 |
| E7 | **Field Worker PWA** | Simple mobile-friendly page: visit checklist, photo upload, GPS stamp, notes | 🟢 P2 |

### 👤 Person F — Analytics & Reporting

| # | Task | Description | Priority |
|---|------|-------------|----------|
| F1 | **KPI Dashboard** | Live stats from DB: total registered, enrolled %, completion rate, avg income change, attendance rate | 🔴 P0 |
| F2 | **Conversion Funnel** | Registered → Assessed → Enrolled → Attending → Completed → Certified → Employed (with drop-off %) | 🔴 P0 |
| F3 | **Attendance Analytics** | Per-batch attendance trends, at-risk beneficiary alerts, dropout prediction | 🟡 P1 |
| F4 | **Outcome Dashboard** | Income before vs after comparison, employment rate post-training, satisfaction scores | 🟡 P1 |
| F5 | **Data Source Indicator** | Every data point shows its source icon (📞 call / 📱 SMS / 🏫 center / 👤 field / 🔗 system) so admins know reliability | 🟡 P1 |

---

## ⚡ Quick Reference: Updated Tech Stack

```
LAYER 1 — AI AGENT (Python)              LAYER 2 — PLATFORM (Node.js)
━━━━━━━━━━━━━━━━━━━━━━━━━━              ━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Python 3.11                            • Node.js 20 + Express 4
• Bhashini SDK (STT/TTS)                 • Neon PostgreSQL (serverless)
• Google Gemini API (LLM)                • Drizzle ORM + Drizzle Kit
• spaCy (NER)                            • Zod (validation)
• Exotel SDK (telephony)                 • JWT (jsonwebtoken + bcrypt)
• FastAPI (internal APIs only)           • React + Vite (frontend)
                                         • Chart.js / Recharts
   Communicates via                      • Leaflet.js (maps)
   REST API (HTTP)
                                         LAYER 3 — TRACKING (Node.js)
         │                               ━━━━━━━━━━━━━━━━━━━━━━━━━━━
         └──────► POST /api/v1/...  ────► • node-cron (scheduling)
                                         • BullMQ + Redis (job queue)
                                         • MSG91 SDK (SMS)
                                         • Same Neon DB connection
```

> [!TIP]
> **Layer 1 stays Python, Layers 2+3 are Node.js.** They're separate Docker containers talking over HTTP. This is a very common pattern — use the best language for each job.
