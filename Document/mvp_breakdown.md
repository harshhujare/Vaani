# 🏗️ VaniSetu MVP — Technical Breakdown
## AI Voice Assistant for Livelihood Mapping & NSQF Skilling

---

## 🗺️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  LAYER 1 — AI AGENT LAYER (Python)                           👥 Person A+B │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────┐               │
│  │ Telephony│→ │ STT      │→ │ Conversation │→ │ NSQF      │               │
│  │ (Exotel) │  │ (Bhashini│  │ AI Engine    │  │ Skill     │               │
│  │          │← │ /Whisper) │← │ (LLM Agent) │← │ Mapper    │               │
│  │ IVR +    │  ├──────────┤  ├──────────────┤  └─────┬─────┘               │
│  │ WhatsApp │  │ TTS      │  │ NLP Pipeline │        │                      │
│  └──────────┘  │ (Bhashini│  │ (Entity Ext.)│        │                      │
│                │ /gTTS)   │  └──────────────┘        │                      │
│                └──────────┘                           │                      │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│                         REST API / WebSocket          │                      │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│                                                       ▼                      │
│  LAYER 2 — PLATFORM LAYER (Node.js)                          👥 Person C+D │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐                 │
│  │ Express.js   │  │ Neon         │  │ Recommendation     │                 │
│  │ Backend      │← │ PostgreSQL   │← │ Engine             │                 │
│  │ (REST APIs)  │→ │ (Serverless  │→ │ (Skill→NSQF→       │                 │
│  │ + Drizzle ORM│  │  + Drizzle)  │  │  Training Match)   │                 │
│  ├──────────────┤  └──────────────┘  └────────────────────┘                 │
│  │ React.js     │                                                            │
│  │ Admin        │  ← Govt officials view dashboards, approve, manage         │
│  │ Dashboard    │                                                            │
│  └──────────────┘                                                            │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│                         Internal APIs / Cron Jobs                            │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│                                                                              │
│  LAYER 3 — HYBRID TRACKING LAYER (Node.js)                   👥 Person E+F │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐                 │
│  │ 🏫 Training  │  │ 📱 SMS Micro │  │ 📊 Analytics &     │                 │
│  │ Center Portal│  │ Surveys +    │  │ Reporting          │                 │
│  │ (Attendance, │  │ 📞 AI Voice  │  │ (Charts, Maps,     │                 │
│  │  Scores,     │  │ Follow-ups + │  │  KPI Dashboard)    │                 │
│  │  Certs)      │  │ 👤 Field App │  │                    │                 │
│  └──────────────┘  └──────────────┘  └────────────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Note:** Layer 1 stays Python (AI/ML libraries are superior). Layers 2 & 3 use Node.js + Express. They communicate via REST APIs as separate services.

---

## 📦 LAYER 1 — AI AGENT LAYER

> **Owner:** Person A (Voice/Telephony) + Person B (AI/NLP)
> **Goal:** Handle the entire voice conversation — from phone ring to structured data output

### 1.1 Components Breakdown

```
LAYER 1 INTERNAL FLOW:
                                                          
  📞 User Calls          🎙️ Voice → Text           🧠 AI Understands           🎯 Skills Mapped
  ─────────────         ──────────────             ────────────────           ───────────────
  Exotel/Twilio    →    Bhashini STT API     →     LLM Conversation    →     NSQF Mapper
  receives call         converts speech            Agent processes           maps skills to
  streams audio         to text in                 text, extracts           NSQF levels
                        detected language          entities (name,          (1-8) using
  TTS responds    ←     Bhashini TTS API    ←      skill, location)   ←     competency rules
  with voice            converts response                                    
                        text to speech                                       
```

### 1.2 Sub-Tasks for Layer 1

#### 👤 Person A — Voice & Telephony Engineer

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| A1 | **Telephony Setup** | Set up Exotel/Twilio account. Configure toll-free number. Build IVR flow for incoming calls | Exotel API / Twilio | 🔴 P0 |
| A2 | **Audio Streaming Pipeline** | Stream incoming call audio to STT engine in real-time. Handle audio chunking, silence detection | WebSocket / Exotel Streams | 🔴 P0 |
| A3 | **STT Integration** | Integrate Bhashini Speech-to-Text API. Handle language detection (Hindi, Tamil, Odia, etc.). Fallback to Whisper if Bhashini fails | Bhashini API, OpenAI Whisper | 🔴 P0 |
| A4 | **TTS Integration** | Integrate Bhashini Text-to-Speech API. Generate natural-sounding responses in user's language. Cache common responses | Bhashini TTS, gTTS fallback | 🔴 P0 |
| A5 | **Call State Manager** | Track call state (greeting → data collection → recommendation → confirmation → end). Handle interruptions, "repeat that", "go back" | Python state machine | 🟡 P1 |
| A6 | **WhatsApp Bot** (v2) | Voice note support via WhatsApp Business API. Same pipeline but async instead of real-time | WhatsApp Business API | 🟢 P2 |

#### 👤 Person B — AI/NLP Engineer

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| B1 | **Conversation Agent** | Design the conversation flow (what questions to ask, in what order). Build the LLM prompt system for guided data extraction | Gemini API / GPT-4 | 🔴 P0 |
| B2 | **Entity Extraction** | Extract structured data from natural speech: name, location, age, occupation, skills, experience, education, income | spaCy / LLM structured output | 🔴 P0 |
| B3 | **Skill Taxonomy** | Build a skill taxonomy database (500+ skills mapped to NSQF sectors). E.g., "furniture making" → Sector: Construction, Sub-sector: Carpentry | JSON/DB taxonomy | 🔴 P0 |
| B4 | **NSQF Level Mapper** | Algorithm to map extracted skills + experience to NSQF levels (1-8) using the 5-parameter framework | Python rules engine + ML | 🔴 P0 |
| B5 | **Conversation Memory** | Maintain context across turns. Remember what user said 3 turns ago. Handle corrections ("No, I said Ranchi not Raipur") | LLM context window / Redis | 🟡 P1 |
| B6 | **Multi-language Prompts** | Create prompt templates in 10+ languages. Ensure AI responds in same language user spoke | i18n templates + Bhashini | 🟡 P1 |

### 1.3 Conversation Flow Design

```
START
  │
  ▼
┌─────────────────────┐
│ 1. GREETING          │  "Namaste! Main PM-AJAY Sahayak hoon..."
│    + Language detect  │  [Detect user's language from first response]
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 2. IDENTITY          │  "Aapka naam? Gaon/sheher? Umra?"
│    Name, Location,   │  [Extract: name, district, state, age]
│    Age               │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 3. LIVELIHOOD        │  "Aap kya kaam karte hain?"
│    Current work,     │  [Extract: occupation, type (formal/informal)]
│    Income            │  "Mahine mein kitna kamate hain?"
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 4. SKILL DEEP-DIVE   │  "Aapko aur kya kaam aata hai?"
│    Hidden skills,    │  [Probe for skills they don't think to mention]
│    Experience years  │  "Kitne saal se kar rahe hain?"
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 5. EDUCATION         │  "Aapne kahan tak padhai ki?"
│    Formal education  │  [Extract: education level]
│    Any prior certs   │  "Koi certificate/training hua hai?"
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 6. NSQF MAPPING      │  [Internal: Map skills → NSQF level]
│    (Backend process) │  [Internal: Find matching training programs]
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ 7. RECOMMENDATION    │  "Aapke hunar ke hisaab se [X] training
│    Training program  │   available hai. Free hai, [Y] months ka,
│    suggestion        │   certificate milega. Register karein?"
└──────────┬──────────┘
           ▼
┌────────┴────────┐
│  YES            │  NO
│  ▼              │  ▼
│ REGISTER        │ "Koi baat nahi. Aapka data save hai.
│ + SMS confirm   │  Kabhi bhi call karein."
│ + Save profile  │  Save profile anyway
└─────────────────┘
```

### 1.4 API Contract (Layer 1 → Layer 2)

Layer 1 sends this JSON to Layer 2's backend after every completed call:

```json
// POST /api/v1/beneficiary/register
{
  "call_id": "CALL-2025-09-26-001",
  "call_duration_seconds": 320,
  "language_detected": "hi",
  
  "beneficiary": {
    "name": "Ramesh Kumar",
    "age": 35,
    "gender": "male",
    "phone": "+91-9XXXXXXXXX",
    "district": "Ranchi",
    "state": "Jharkhand",
    "village": "Bara Ghaghra",
    "caste_category": "SC",
    "education_level": "8th_pass",
    "current_monthly_income": 6000,
    "household_size": 5,
    "bpl_status": true
  },
  
  "skills_extracted": [
    {
      "skill_name": "Carpentry - Furniture Making",
      "sector": "Construction",
      "sub_sector": "Woodwork",
      "experience_years": 15,
      "is_primary": true,
      "confidence_score": 0.92,
      "nsqf_level_mapped": 4,
      "sub_skills": ["joinery", "finishing", "wood_selection", "measurement"]
    },
    {
      "skill_name": "Basic Plumbing",
      "sector": "Construction",
      "sub_sector": "Plumbing",
      "experience_years": 3,
      "is_primary": false,
      "confidence_score": 0.71,
      "nsqf_level_mapped": 2,
      "sub_skills": ["pipe_fitting"]
    }
  ],
  
  "nsqf_assessment": {
    "primary_nsqf_level": 4,
    "assessment_basis": "experience_years + skill_depth + sub_skill_count",
    "recommended_training_level": 5,
    "recommended_sector": "Construction"
  },
  
  "training_preference": {
    "willing_to_train": true,
    "preferred_timing": "morning",
    "max_travel_distance_km": 15,
    "preferred_language": "hi"
  },
  
  "conversation_transcript": "...(full transcript for audit)...",
  "ai_confidence_overall": 0.87
}
```

---

## 📦 LAYER 2 — PLATFORM LAYER

> **Owner:** Person C (Backend + DB) + Person D (Frontend + Recommendation)
> **Goal:** Store data, serve APIs, show dashboards, match beneficiaries to training

### 2.1 Components Breakdown

```
LAYER 2 INTERNAL FLOW:

  📥 API receives          🗄️ Stores in DB          🎯 Matches training        📊 Shows dashboard
  data from Layer 1       ────────────────         ──────────────────        ─────────────────
  Express.js       →      Neon PostgreSQL  →       Recommendation      →    React.js Admin
  endpoints +             (Serverless) via         Engine queries             Panel shows stats,
  Zod validation          Drizzle ORM              available programs,        maps, beneficiary
                                                   ranks by fit score         lists, approvals
```

### 2.2 Sub-Tasks for Layer 2

#### 👤 Person C — Backend & Database Engineer

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| C1 | **Database Schema** | Design Drizzle ORM schema + run migrations on Neon PostgreSQL | Neon PostgreSQL + Drizzle ORM | 🔴 P0 |
| C2 | **Express Server** | Set up Node.js + Express project with proper structure (routes, controllers, middleware) | Node.js, Express | 🔴 P0 |
| C3 | **Beneficiary APIs** | CRUD endpoints: register, update, get, list, search, filter by district/skill/NSQF level | Express + Zod validation | 🔴 P0 |
| C4 | **Training Program APIs** | CRUD for training programs. Bulk import from CSV. Filter by sector, NSQF level, district | Express + Drizzle | 🔴 P0 |
| C5 | **Enrollment APIs** | Enroll beneficiary in training. Track status (enrolled → attending → completed → certified) | Express + Drizzle | 🟡 P1 |
| C6 | **Attendance APIs** | Training center marks daily attendance per batch. Auto-flag dropouts (5+ absent days) | Express + Drizzle | 🔴 P0 |
| C7 | **Auth & RBAC** | JWT-based auth. Roles: admin, district_officer, state_officer, training_center, viewer | jsonwebtoken + bcrypt | 🟡 P1 |
| C8 | **SMS Integration** | Send SMS confirmations to beneficiaries after registration/enrollment via MSG91 | MSG91 Node.js SDK | 🟡 P1 |

#### 👤 Person D — Frontend & Recommendation Engine

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| D1 | **Admin Dashboard Layout** | Main layout: sidebar, topbar, routing. Pages: Dashboard, Beneficiaries, Programs, Tracking, Analytics | React.js + React Router | 🔴 P0 |
| D2 | **Dashboard Home** | Key stats: total beneficiaries, skills mapped, enrollments, completion rate. Charts for trends | React + Chart.js/Recharts | 🔴 P0 |
| D3 | **Beneficiary List View** | Searchable, filterable table. Columns: name, district, skills, NSQF level, status. Click to view profile | React Table / AG Grid | 🔴 P0 |
| D4 | **Beneficiary Detail View** | Full profile: personal info, extracted skills, NSQF mapping, training history, call recording link | React | 🟡 P1 |
| D5 | **Training Programs Manager** | List/add/edit training programs. Fields: name, sector, NSQF level, duration, district, capacity, dates | React + Forms | 🟡 P1 |
| D6 | **Training Center Portal** | Simple page for training center staff: mark attendance, record scores, upload certs, flag dropouts | React (separate login role) | 🔴 P0 |
| D7 | **Recommendation Engine** | Algorithm: match beneficiary skills + NSQF level + location → rank available programs by fit score | Node.js (Express service) | 🔴 P0 |
| D8 | **District Map View** | India map showing beneficiary density, skill clusters, training center locations per district | Leaflet.js / React-Leaflet | 🟢 P2 |

### 2.3 Database Schema

```js
// ════════════════════════════════════════════════════════════
// DATABASE SCHEMA — Drizzle ORM + Neon PostgreSQL
// File: backend/src/db/schema.js
// ════════════════════════════════════════════════════════════

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

// ── 1. Beneficiaries (the people we serve) ──
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

// ── 2. Skills (extracted from conversations) ──
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

// ── 3. Training Programs (available courses) ──
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

// ── 4. Enrollments (beneficiary ↔ training link) ──
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

// ── 5. Call Logs (every voice interaction) ──
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

// ══════════════════════════════════════════
// LAYER 3 TABLES — Hybrid Tracking
// ══════════════════════════════════════════

// ── 6. Attendance (Training center fills daily) ──  🆕
export const attendance = pgTable('attendance', {
  id:              uuid('id').primaryKey().defaultRandom(),
  enrollmentId:    uuid('enrollment_id').references(() => enrollments.id),
  date:            date('date').notNull(),
  isPresent:       boolean('is_present').default(false),
  markedBy:        varchar('marked_by', { length: 100 }),  // training center staff username
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── 7. Follow-ups (scheduled automated contacts) ──
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

// ── 8. Outcomes (did life actually improve?) ──
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
  dataSource:      varchar('data_source', { length: 20 }),  // 'ai_call', 'sms', 'field_worker', 'training_center'
  createdAt:       timestamp('created_at').defaultNow(),
});

// ── 9. NSQF Skill Taxonomy (reference/seed data) ──
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

**Neon DB Connection Setup:**

```js
// backend/src/config/db.js
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import * as schema from '../db/schema.js';

const sql = neon(process.env.DATABASE_URL);  // Neon connection string
export const db = drizzle(sql, { schema });
```

### 2.4 Recommendation Engine Logic

```
INPUT: beneficiary_skills + beneficiary_location
OUTPUT: ranked list of matching training_programs

ALGORITHM:
──────────

Score = (sector_match × 0.3) 
      + (nsqf_level_fit × 0.25) 
      + (distance_score × 0.2) 
      + (capacity_available × 0.15) 
      + (timing_score × 0.1)

WHERE:
  sector_match     = 1.0 if exact sector match, 0.5 if same parent sector, 0 otherwise
  nsqf_level_fit   = 1.0 if program is 1 level above current, 0.7 if same level, 0.3 if 2+ above
  distance_score   = 1.0 if same district, 0.5 if adjacent district, 0.2 if same state
  capacity_available = 1.0 if <50% full, 0.5 if <80% full, 0.1 if >80% full
  timing_score     = 1.0 if matches preference, 0.5 otherwise

RETURN: Top 3 programs sorted by score DESC
```

### 2.5 Key API Endpoints

```
BASE URL: /api/v1

── Beneficiary ──────────────────────────────────────────
POST   /beneficiary/register          ← Layer 1 sends data here
GET    /beneficiary/{id}              ← Get full profile
GET    /beneficiaries                 ← List all (paginated, filterable)
PUT    /beneficiary/{id}              ← Update profile
GET    /beneficiary/{id}/skills       ← Get skills list
GET    /beneficiary/{id}/enrollments  ← Get training history

── Training Programs ────────────────────────────────────
POST   /programs                      ← Create program
GET    /programs                      ← List (filter by sector, NSQF, district)
GET    /programs/{id}                 ← Get program details
PUT    /programs/{id}                 ← Update program
POST   /programs/bulk-import          ← CSV import

── Recommendation ───────────────────────────────────────
GET    /recommend/{beneficiary_id}    ← Get top 3 training matches
POST   /enroll                        ← Enroll beneficiary in program

── Analytics (Layer 3 uses these) ───────────────────────
GET    /analytics/dashboard           ← Aggregate stats
GET    /analytics/district/{name}     ← Per-district breakdown
GET    /analytics/skills-heatmap      ← Skill distribution
GET    /analytics/funnel              ← Registered→Enrolled→Completed funnel

── Tracking (Layer 3) ───────────────────────────────────
POST   /followup/schedule             ← Schedule a follow-up
GET    /followups/pending             ← Get pending follow-ups
POST   /outcome                       ← Record outcome data
GET    /outcomes/{beneficiary_id}     ← Get outcome history
```

---

## 📦 LAYER 3 — HYBRID TRACKING & IMPLEMENTATION LAYER

> **Owner:** Person E (Tracking System) + Person F (Analytics & Reporting)
> **Goal:** Track beneficiary progress using **5 data sources** (NOT just voice calls), automate follow-ups, measure real outcomes

### 3.1 Why Hybrid? — Voice-Only Tracking Doesn't Work

```
❌ WHY WE CAN'T JUST CALL EVERYONE:

  "Are you attending training?"     → Beneficiary can LIE (says yes, but isn't going)
  "Did you complete training?"      → We need PROOF, not self-reporting
  "Did you get certificate?"        → Certificate is issued by training center, NOT beneficiary
  "Did you get a job?"              → Beneficiary might not pick up 3 months later
  Calling 10,000+ people monthly    → Not scalable even for AI
```

### 3.2 The 5 Data Sources

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
│   completion,       (no smartphone    data (income,    staff (10%       │
│   grades, certs     needed)           satisfaction)    random sample)   │
│                                                                         │
│                          SOURCE 5                                       │
│                          ─────────                                      │
│                          🔗 Govt System Integration                     │
│                          PM-AJAY Portal API / bulk                      │
│                          data sync for certificate                      │
│                          verification                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Data Source Matrix — WHO provides WHAT at EACH stage

| Lifecycle Stage | Primary Data Source | What Data | Secondary Source |
|----------------|-------------------|-----------|------------------|
| **REGISTERED** | 📞 AI Voice Call (Layer 1) | Name, skills, location, income | — |
| **ASSESSED** | 🧠 AI Engine (Auto) | NSQF level, training match | — |
| **ENROLLED** | 🏫 Training Center Portal | "Ramesh is enrolled in batch #12" | 📱 SMS to beneficiary confirming |
| **ATTENDING** | 🏫 Training Center Portal | Daily attendance (mark present/absent) | 👤 Field worker spot-check |
| **DROPPED** | 🏫 Training Center Portal | "Absent 5+ days" → auto-flag | 📞 AI calls to ask why + convince to return |
| **COMPLETED** | 🏫 Training Center Portal | "Completed training, scored 78%" | — |
| **CERTIFIED** | 🔗 Govt System / Training Center | Certificate ID, NSQF level, date | 🏫 Training center uploads cert |
| **EMPLOYED** | 📞 AI Voice Follow-up + 📱 SMS | "Got job, earning ₹12K/month" | 👤 Field worker verification (sample) |

### 3.4 Training Center Portal (Source 1 — Most Important)

Simple web form that training center staff fill daily:

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

### 3.5 SMS Micro-Surveys (Source 2 — Works on ANY Phone)

Dead-simple SMS messages needing only a **1-digit reply**:

```
TRAINING START CONFIRMATION:
→ "Ramesh ji, aapki carpentry training kal se hai.
   Kya aap aa rahe hain? Reply: 1=Haan, 2=Nahi"
← Reply: 1
✅ Status: Confirmed

MID-TRAINING CHECK:
→ "Training kaisi chal rahi hai?
   Reply: 1=Bahut acchi, 2=Theek, 3=Problem hai"
← Reply: 3
🚨 Alert → District officer notified → AI calls beneficiary

POST-TRAINING INCOME CHECK (30 days later):
→ "Kya aapki income badhi hai training ke baad?
   Reply: 1=Haan, 2=Nahi, 3=Wahi hai"
← Reply: 1
✅ Outcome recorded: income increased
```

### 3.6 When to Use Each Source

| Use AI Calls For (Expensive) | Use SMS For (Cheap) | Use Training Center Portal For |
|------------------------------|--------------------|---------------------------------|
| ✅ Post-training outcome survey | ✅ Simple yes/no checks | ✅ Daily attendance |
| ✅ Dropout investigation | ✅ Routine reminders | ✅ Assessment scores |
| ✅ 90/180-day impact assessment | ✅ Confirmation messages | ✅ Certificate uploads |
| ✅ Beneficiary didn't respond to SMS 2x | ✅ Quick satisfaction checks | ✅ Dropout flagging |

### 3.7 Sub-Tasks for Layer 3

#### 👤 Person E — Tracking & Hybrid Data Collection

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| E1 | **Training Center Portal** | Simple web form: login, mark attendance, record scores, upload certs. React page in admin dashboard | React (separate role in dashboard) | 🔴 P0 |
| E2 | **Attendance API** | `POST /api/v1/attendance` — training center marks daily attendance per batch | Express + Drizzle | 🔴 P0 |
| E3 | **Auto Dropout Detection** | Cron job: if absent 5+ consecutive days → status = 'at_risk' → alert officer + trigger AI call | node-cron + Express | 🔴 P0 |
| E4 | **SMS Micro-Survey Engine** | Send template SMS, parse numeric replies (1/2/3), update DB. Using MSG91 2-way SMS | MSG91 Node.js SDK | 🟡 P1 |
| E5 | **Follow-up Scheduler** | node-cron checks `followups` table every 15 min, executes pending SMS/calls | node-cron + BullMQ | 🔴 P0 |
| E6 | **Outcome Collection** | Multi-source: AI call data + SMS survey data + field worker data → merged into `outcomes` table | Express + Drizzle | 🟡 P1 |
| E7 | **Field Worker PWA** | Simple mobile-friendly page: visit checklist, photo upload, GPS stamp, notes | React (PWA) | 🟢 P2 |
| E8 | **Alert System** | Alert district officers when: drop-out detected, program full, outcome scores low | Email/SMS alerts | 🟢 P2 |

#### 👤 Person F — Analytics & Reporting

| # | Task | Description | Tech | Priority |
|---|------|-------------|------|----------|
| F1 | **KPI Dashboard** | Live stats: total registered, enrolled %, completion rate, avg income change, attendance rate | React + Chart.js | 🔴 P0 |
| F2 | **Conversion Funnel** | Visual funnel: Registered → Assessed → Enrolled → Attending → Completed → Certified → Employed | React + Recharts | 🔴 P0 |
| F3 | **Attendance Analytics** | Per-batch attendance trends, at-risk beneficiary alerts, dropout prediction | React + Chart.js | 🟡 P1 |
| F4 | **District Heatmap** | India map colored by beneficiary density / completion rate per district | Leaflet.js + GeoJSON | 🟡 P1 |
| F5 | **Outcome Dashboard** | Income before vs after, employment rate post-training, satisfaction scores by data source | React + Recharts | 🟡 P1 |
| F6 | **Data Source Indicator** | Every data point shows its source icon (📞/📱/🏫/👤/🔗) so admins know reliability | React component | 🟡 P1 |
| F7 | **Report Generator** | Auto-generate monthly PDF reports for district/state officers | jsPDF / Puppeteer | 🟢 P2 |
| F8 | **Fund Utilization Tracker** | Track GIA funding spent per district, per program, per beneficiary. ROI metrics | React + backend APIs | 🟢 P2 |

### 3.3 Beneficiary Lifecycle State Machine

```
                    ┌──────────────┐
                    │  REGISTERED  │ ← Initial state (after voice call)
                    └──────┬───────┘
                           │ AI assessment complete
                           ▼
                    ┌──────────────┐
                    │   ASSESSED   │ ← Skills mapped, NSQF level assigned
                    └──────┬───────┘
                           │ Training program matched & accepted
                           ▼
                    ┌──────────────┐
                    │   ENROLLED   │ ← Registered for a training program
                    └──────┬───────┘
                           │ Training begins
                    ┌──────┴───────┐
                    ▼              ▼
             ┌──────────┐  ┌───────────┐
             │ ATTENDING │  │  DROPPED  │ ← Didn't attend / left early
             └─────┬────┘  └───────────┘
                   │ Training completed
                   ▼
            ┌──────────────┐
            │  COMPLETED   │ ← Finished the training
            └──────┬───────┘
                   │ Exam passed, certificate issued
                   ▼
            ┌──────────────┐
            │  CERTIFIED   │ ← NSQF certificate received
            └──────┬───────┘
                   │ Follow-up: got a job / started business
                   ▼
            ┌──────────────┐
            │   EMPLOYED   │ ← Using new skills, income increased
            └──────────────┘
```

### 3.4 Follow-up Schedule Template

| Trigger Event | Delay | Action | Channel | Purpose |
|--------------|-------|--------|---------|---------|
| Registration | Immediately | "Aapka registration ho gaya" | SMS | Confirmation |
| Registration | +24 hours | Enrollment reminder if not enrolled | SMS | Nudge |
| Enrollment | Immediately | Training details + date + location | SMS | Info |
| Training Start | -1 day | "Kal se training shuru hai" | SMS | Reminder |
| Training Start | +7 days | "Training kaisi chal rahi hai?" | AI Call | Check-in |
| Training Mid-point | Mid-training | Satisfaction & progress check | AI Call | Monitor |
| Training Complete | +1 day | "Congratulations! Certificate ready" | SMS | Celebrate |
| Training Complete | +30 days | "Income mein koi badlav aaya?" | AI Call | Outcome |
| Training Complete | +90 days | Detailed outcome survey | AI Call | Impact |
| Training Complete | +180 days | Long-term impact assessment | AI Call | Impact |

---

## 🛠️ Tech Stack Summary

| Layer | Component | Technology | Why This? |
|-------|-----------|-----------|-----------|
| **L1** | Telephony | Exotel | Indian telecom API, toll-free support, IVR |
| **L1** | STT | Bhashini API | Govt platform, 22+ Indian languages, free |
| **L1** | TTS | Bhashini API | Same platform, consistent voice quality |
| **L1** | LLM | Gemini API | Best multilingual support, free tier available |
| **L1** | NLP | spaCy + custom NER | Entity extraction for Indian names, locations |
| **L1** | Framework | Python (FastAPI internal) | AI/ML libraries are superior in Python |
| **L2** | Backend | **Node.js + Express** | Team preference, JS everywhere for L2+L3 |
| **L2** | Database | **Neon PostgreSQL** (serverless) | Auto-scaling, no infra management, free tier |
| **L2** | ORM | **Drizzle ORM** + Drizzle Kit | Type-safe, SQL-like syntax, great Neon support |
| **L2** | Validation | **Zod** | Runtime validation for Node.js, pairs with Drizzle |
| **L2** | Auth | **jsonwebtoken + bcrypt** | Standard Node.js JWT auth |
| **L2** | Frontend | React.js + Vite | Fast dev, component reuse, rich ecosystem |
| **L2** | Charts | Chart.js / Recharts | Easy integration with React |
| **L2** | Maps | Leaflet.js | Free, works with Indian district GeoJSON |
| **L3** | Scheduling | **node-cron** | Simple cron jobs in Node.js |
| **L3** | Job Queue | **BullMQ + Redis** | Reliable async job processing for follow-ups |
| **L3** | SMS | MSG91 | Reliable Indian SMS delivery, 2-way SMS support |
| **L3** | Caching | Redis | Fast session store, pub/sub for events |
| **All** | Deployment | Docker + Docker Compose | Consistent across all machines |
| **All** | CI/CD | GitHub Actions | Free for open source |

> **Note:** Layer 1 stays **Python** (AI/ML ecosystem). Layers 2+3 use **Node.js**. They're separate Docker containers talking over REST APIs — this is a standard microservice pattern.

---

## 📅 4-Week Sprint Plan

### Week 1: Foundation
| Person | Focus |
|--------|-------|
| A | Exotel account setup + basic IVR flow + audio streaming to endpoint |
| B | Conversation flow design + Gemini API integration + first working prompt |
| C | Neon PostgreSQL setup + Drizzle schema + Express project + beneficiary CRUD APIs |
| D | React project setup + dashboard layout + dummy data visualization |
| E | Training center portal UI (attendance form) + attendance API |
| F | KPI card components + Chart.js setup with mock data |

### Week 2: Core Integration
| Person | Focus |
|--------|-------|
| A | STT (Bhashini) integration + TTS integration + end-to-end voice test |
| B | Entity extraction pipeline + skill taxonomy DB (50 skills) + NSQF mapper v1 |
| C | Training programs API + enrollment API + Zod validation |
| D | Beneficiary list page + detail page + recommendation engine v1 |
| E | Follow-up scheduler (node-cron) + SMS micro-survey engine (MSG91) |
| F | Conversion funnel chart + connect dashboard to real APIs |

### Week 3: End-to-End Flow
| Person | Focus |
|--------|-------|
| A+B | Full call flow: call → STT → AI conversation → extract → respond → save to DB |
| C | Auth (JWT) + API hardening + error handling + Drizzle migrations |
| D | Training center portal + programs page + map view (Leaflet) |
| E | Auto dropout detection cron + multi-source outcome collection |
| F | District heatmap + attendance analytics + data source indicators |

### Week 4: Polish & Demo
| Person | Focus |
|--------|-------|
| A | Call quality testing + edge cases (noise, silence, interruptions) |
| B | Multi-language testing (Hindi + 2 more) + accuracy tuning |
| C | Performance optimization + API docs + Neon connection pooling |
| D | UI polish + responsive design + demo flow preparation |
| E | Field worker PWA + alert system + end-to-end tracking demo |
| F | Report generation + final dashboard polish + demo prep |

---

## 🔗 Integration Points (How Layers Talk)

```
LAYER 1  ──POST /api/v1/beneficiary/register──►  LAYER 2 (Backend)
LAYER 1  ──POST /api/v1/call-logs──────────────►  LAYER 2 (Backend)

LAYER 2  ──GET  /api/v1/recommend/{id}─────────►  LAYER 2 (Recommendation Engine)
LAYER 2  ──POST /api/v1/followup/schedule──────►  LAYER 3 (Scheduler)

LAYER 3  ──GET  /api/v1/analytics/dashboard────►  LAYER 2 (Backend)
LAYER 3  ──triggers outbound call──────────────►  LAYER 1 (Voice AI)
LAYER 3  ──POST /api/v1/outcome────────────────►  LAYER 2 (Backend)
```

> [!TIP]
> **All 3 layers share the same PostgreSQL database** but access different tables. Layer 1 WRITES beneficiary + skills data. Layer 2 READS/WRITES everything. Layer 3 READS beneficiary data + WRITES follow-ups and outcomes.

---

## ✏️ Next Steps

Once you approve this breakdown:
1. I can **generate the project boilerplate** (Express + React + Drizzle + Docker Compose)
2. Create the **Drizzle migration scripts** for Neon PostgreSQL
3. Build the **conversation flow prompts** for Layer 1
4. Set up the **NSQF skill taxonomy** seed data
5. Scaffold the **Training Center Portal** UI

**Which layer should we start building first?**
