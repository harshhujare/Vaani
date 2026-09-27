# 🔌 Integration Guide — VaniSetu Platform APIs
## For Developer A (AI Agent Layer) & Developer B (Recommendation + Tracking)

> **Platform Base URL:** `http://localhost:3001/api/v1`
> **Production URL:** `https://api.vanisetu.in/api/v1` (TBD)

---

## 📑 Table of Contents

1. [Authentication](#-authentication)
2. [Developer A — AI Agent Layer Integration](#-developer-a--ai-agent-layer-python)
3. [Developer B — Recommendation Engine Integration](#-developer-b--recommendation-engine)
4. [Developer B — Tracking & Follow-up Integration](#-developer-b--tracking--follow-up-system)
5. [Webhook Events](#-webhook-events-future)
6. [Error Handling](#-error-handling)
7. [Database Access Rules](#-database-access-rules)

---

## 🔐 Authentication

### For Developer A (Layer 1 — Python Service)

Your service authenticates using an **API Key** (no JWT needed):

```
Header: X-API-Key: <provided-key>
```

You will receive this key from the platform team. Use it in all requests:

```python
# Python example
import requests

PLATFORM_URL = "http://localhost:3001/api/v1"
API_KEY = "vanisetu-layer1-secret-key-2025"  # you will get this

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

response = requests.post(
    f"{PLATFORM_URL}/beneficiary/register",
    json=payload,
    headers=headers
)
```

### For Developer B (Recommendation + Tracking — Node.js)

Your service also uses an **API Key** for server-to-server calls:

```js
// Node.js example
const PLATFORM_URL = "http://localhost:3001/api/v1";
const API_KEY = "vanisetu-devb-secret-key-2025";  // you will get this

const response = await fetch(`${PLATFORM_URL}/recommend/data/${beneficiaryId}`, {
    headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
});
```

---

## 👤 Developer A — AI Agent Layer (Python)

### What You Send to Platform

After every completed voice call, your system sends the extracted data to the platform.

### Endpoint 1: Register Beneficiary

```
POST /api/v1/beneficiary/register
```

**When to call:** After every completed voice call where you successfully extracted beneficiary data.

**Request Body:**

```json
{
  "call_id": "CALL-2025-09-26-001",
  "call_duration_seconds": 320,
  "language_detected": "hi",
  
  "beneficiary": {
    "name": "Ramesh Kumar",
    "age": 35,
    "gender": "male",
    "phone": "+91-9876543210",
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
      "sub_skills": ["joinery", "finishing", "wood_selection"]
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
  
  "conversation_transcript": "Full transcript text here...",
  "ai_confidence_overall": 0.87
}
```

**Success Response (201):**

```json
{
  "success": true,
  "data": {
    "beneficiary_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "registered",
    "skills_saved": 2,
    "call_log_id": "660e8400-e29b-41d4-a716-446655440001"
  },
  "message": "Beneficiary registered successfully"
}
```

**Duplicate Phone Response (409):**

```json
{
  "success": false,
  "data": {
    "existing_beneficiary_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Beneficiary with this phone already exists. Use PUT to update."
}
```

### Endpoint 2: Update Existing Beneficiary (Re-call)

When a beneficiary calls again and provides updated info:

```
PUT /api/v1/beneficiary/:id
```

```json
{
  "skills_extracted": [ ... ],
  "nsqf_assessment": { ... },
  "ai_confidence_overall": 0.90
}
```

### Endpoint 3: Store Call Log

Every call (successful or not) should be logged:

```
POST /api/v1/call-logs
```

```json
{
  "beneficiary_id": "550e8400-...",
  "call_id": "CALL-2025-09-26-001",
  "call_type": "inbound",
  "duration_seconds": 320,
  "language": "hi",
  "transcript": "Full conversation transcript...",
  "ai_confidence": 0.87,
  "raw_audio_url": "https://storage.example.com/calls/CALL-001.wav"
}
```

### Endpoint 4: Get NSQF Taxonomy (For Your Skill Mapping)

You can fetch the skill taxonomy to improve your mapping accuracy:

```
GET /api/v1/taxonomy?sector=Construction
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "sector": "Construction",
      "sub_sector": "Carpentry",
      "skill_name": "Furniture Maker",
      "nsqf_level": 4,
      "qualification_pack": "CON/Q0302",
      "keywords": ["furniture", "lakdi", "carpenter", "wood", "almari"]
    }
  ]
}
```

> **Tip:** Use the `keywords` array to match what beneficiaries say in their language to the correct skill in the taxonomy.

### Endpoint 5: Outbound Call Trigger (Layer 3 → Layer 1)

Developer B's tracking system will trigger outbound calls through your Layer 1 service. **You need to expose an endpoint** that accepts:

```
POST http://your-layer1-service:5000/api/outbound-call
```

```json
{
  "beneficiary_id": "550e8400-...",
  "phone": "+91-9876543210",
  "purpose": "post_training_followup",
  "language": "hi",
  "script_type": "outcome_survey"
}
```

This is YOUR endpoint to build. The platform will trigger it when Dev B's scheduler runs.

### Quick Reference for Developer A

| Action | Method | Endpoint | When |
|--------|--------|----------|------|
| Register new beneficiary | POST | `/beneficiary/register` | After every completed call |
| Update existing beneficiary | PUT | `/beneficiary/:id` | When beneficiary calls again |
| Log a call | POST | `/call-logs` | After EVERY call (even failed ones) |
| Get skill taxonomy | GET | `/taxonomy` | On startup / periodically cache |
| Check if phone exists | GET | `/beneficiary/phone/:phone` | Before registration to avoid duplicates |

---

## 🎯 Developer B — Recommendation Engine

### How Recommendation Works (Architecture)

```
Platform stores data → Dev B's engine reads it → Computes match → Posts result back

┌──────────┐     GET /recommend/data/:id      ┌──────────────────┐
│          │ ──────────────────────────────►   │                  │
│ Platform │                                   │  Recommendation  │
│ (Layer 2)│   POST /recommend/result          │  Engine (Dev B)  │
│          │ ◄──────────────────────────────   │                  │
└──────────┘                                   └──────────────────┘
```

### Endpoint 1: Get Beneficiary Data for Recommendation

```
GET /api/v1/recommend/data/:beneficiaryId
```

**Response:**

```json
{
  "success": true,
  "data": {
    "beneficiary": {
      "id": "550e8400-...",
      "district": "Ranchi",
      "state": "Jharkhand",
      "education_level": "8th_pass",
      "language": "hi"
    },
    "skills": [
      {
        "skill_name": "Carpentry - Furniture Making",
        "sector": "Construction",
        "sub_sector": "Woodwork",
        "nsqf_level": 4,
        "experience_years": 15,
        "is_primary": true
      }
    ],
    "training_preference": {
      "willing_to_train": true,
      "preferred_timing": "morning",
      "max_travel_distance_km": 15
    },
    "available_programs": [
      {
        "id": "prog-001",
        "name": "Advanced Carpentry & Furniture Design",
        "sector": "Construction",
        "sub_sector": "Woodwork",
        "nsqf_level": 5,
        "duration_days": 90,
        "district": "Ranchi",
        "capacity": 30,
        "enrolled_count": 12,
        "start_date": "2025-11-01"
      },
      {
        "id": "prog-002",
        "name": "Construction Supervisor Training",
        "sector": "Construction",
        "nsqf_level": 6,
        "district": "Ranchi",
        "capacity": 20,
        "enrolled_count": 18,
        "start_date": "2025-10-15"
      }
    ]
  }
}
```

> **Note:** The platform pre-fetches available programs in the same district + adjacent districts. Your engine only needs to SCORE and RANK them.

### Endpoint 2: Post Recommendation Result

After your engine computes the best matches, post the result back:

```
POST /api/v1/recommend/result
```

```json
{
  "beneficiary_id": "550e8400-...",
  "recommendations": [
    {
      "program_id": "prog-001",
      "match_score": 0.92,
      "reason": "Exact sector match, NSQF level +1, same district"
    },
    {
      "program_id": "prog-002",
      "match_score": 0.65,
      "reason": "Same sector, NSQF level +2 (stretch), almost full"
    }
  ],
  "top_recommendation_id": "prog-001"
}
```

### Endpoint 3: Get Available Programs (For Matching)

If you need to query programs directly:

```
GET /api/v1/programs?sector=Construction&nsqf_level=5&district=Ranchi&is_active=true
```

### Scoring Algorithm (Reference)

This is the algorithm you implement. The platform provides the data, you compute the score:

```
Score = (sector_match × 0.3) 
      + (nsqf_level_fit × 0.25) 
      + (distance_score × 0.2) 
      + (capacity_available × 0.15) 
      + (timing_score × 0.1)

WHERE:
  sector_match     = 1.0 exact, 0.5 parent sector, 0 none
  nsqf_level_fit   = 1.0 if +1 above, 0.7 same, 0.3 if +2
  distance_score   = 1.0 same district, 0.5 adjacent, 0.2 same state
  capacity_available = 1.0 if <50% full, 0.5 if <80%, 0.1 if >80%
  timing_score     = 1.0 matches preference, 0.5 otherwise
```

### Quick Reference for Recommendation Engine

| Action | Method | Endpoint | When |
|--------|--------|----------|------|
| Get beneficiary + programs data | GET | `/recommend/data/:id` | When a new registration comes in |
| Post recommendation result | POST | `/recommend/result` | After computing match scores |
| Query programs by filters | GET | `/programs?sector=X&district=Y` | If you need additional filtering |
| Get NSQF taxonomy | GET | `/taxonomy` | For skill mapping reference |

---

## 📊 Developer B — Tracking & Follow-up System

### How Tracking Integrates

```
Platform stores beneficiary lifecycle → Dev B reads pending tasks → Executes (SMS/Call) → Reports back

┌──────────┐    GET /followups/pending     ┌──────────────────┐
│          │ ──────────────────────────►   │                  │
│ Platform │                               │  Tracking System │
│ (Layer 2)│   PATCH /followups/:id        │  (Dev B)         │
│          │ ◄──────────────────────────   │                  │
│          │   POST /outcomes              │  - node-cron     │
│          │ ◄──────────────────────────   │  - MSG91 SMS     │
└──────────┘                               │  - BullMQ        │
                                           └──────────────────┘
```

### Endpoint 1: Schedule a Follow-up

When the platform registers a beneficiary or changes enrollment status, Dev B may need to schedule follow-ups:

```
POST /api/v1/followups
```

```json
{
  "beneficiary_id": "550e8400-...",
  "followup_type": "sms",
  "scheduled_at": "2025-10-02T09:00:00Z",
  "purpose": "enrollment_reminder",
  "message_template": "registration_confirm"
}
```

### Endpoint 2: Get Pending Follow-ups

Your cron job polls this every 15 minutes:

```
GET /api/v1/followups/pending
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "fu-001",
      "beneficiary_id": "550e8400-...",
      "phone": "+91-9876543210",
      "followup_type": "sms",
      "scheduled_at": "2025-10-02T09:00:00Z",
      "purpose": "registration_confirm",
      "language": "hi"
    },
    {
      "id": "fu-002",
      "beneficiary_id": "660e8400-...",
      "phone": "+91-9876543211",
      "followup_type": "call",
      "scheduled_at": "2025-10-02T09:15:00Z",
      "purpose": "dropout_investigation",
      "language": "hi"
    }
  ]
}
```

### Endpoint 3: Update Follow-up Status

After executing a follow-up (SMS sent or call made):

```
PATCH /api/v1/followups/:id
```

```json
{
  "status": "completed",
  "executed_at": "2025-10-02T09:01:23Z",
  "response_summary": "SMS delivered. Reply received: 1 (confirmed)"
}
```

### Endpoint 4: Post Outcome Data

After collecting outcome data (from AI call, SMS reply, or field worker):

```
POST /api/v1/outcomes
```

```json
{
  "beneficiary_id": "550e8400-...",
  "enrollment_id": "enroll-001",
  "check_date": "2025-12-15",
  "income_before": 6000,
  "income_after": 12000,
  "employment_status": "self_employed",
  "is_using_skill": true,
  "satisfaction": 4,
  "notes": "Started making furniture independently. Getting orders from local shops.",
  "data_source": "ai_call"
}
```

**Valid `data_source` values:** `"ai_call"`, `"sms"`, `"field_worker"`, `"training_center"`

### Endpoint 5: Get Dropout Candidates

Your auto-dropout detection cron queries this:

```
GET /api/v1/attendance/at-risk?absent_days=5
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "beneficiary_id": "550e8400-...",
      "name": "Meena Devi",
      "phone": "+91-9876543212",
      "program_name": "Advanced Carpentry",
      "consecutive_absent_days": 6,
      "last_attended": "2025-10-09",
      "enrollment_id": "enroll-003"
    }
  ]
}
```

When you detect at-risk beneficiaries:
1. Send an alert SMS to the district officer
2. Trigger an outbound AI call via Layer 1's API
3. Update the enrollment status to `"dropped"` if no response after 2 attempts

### Endpoint 6: Get Beneficiary Status (for Lifecycle Transitions)

```
GET /api/v1/beneficiary/:id
```

Check `status` field. Valid transitions:

```
registered → assessed → enrolled → attending → completed → certified → employed
                                  → dropped (can re-enter at enrolled)
```

To update status:

```
PATCH /api/v1/beneficiary/:id/status
```

```json
{
  "status": "enrolled",
  "updated_by": "system_auto"
}
```

### Quick Reference for Tracking System

| Action | Method | Endpoint | When |
|--------|--------|----------|------|
| Schedule follow-up | POST | `/followups` | After registration / status change |
| Get pending follow-ups | GET | `/followups/pending` | Every 15 min (cron) |
| Update follow-up result | PATCH | `/followups/:id` | After SMS sent / call completed |
| Post outcome data | POST | `/outcomes` | After collecting income/employment data |
| Check at-risk students | GET | `/attendance/at-risk?absent_days=5` | Daily cron |
| Update beneficiary status | PATCH | `/beneficiary/:id/status` | On lifecycle transitions |
| Trigger outbound call | POST | Layer 1's endpoint | For dropout investigation / outcome survey |

---

## ❌ Error Handling

All error responses follow this format:

```json
{
  "success": false,
  "data": null,
  "message": "Human-readable error description",
  "errors": [
    { "field": "phone", "message": "Must be a valid Indian phone number" }
  ]
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET / PATCH |
| 201 | Created | Successful POST (new resource created) |
| 400 | Bad Request | Validation failed (check `errors` array) |
| 401 | Unauthorized | Missing or invalid API key / JWT token |
| 403 | Forbidden | Valid auth but insufficient role permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate entry (e.g., phone already registered) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error (report to platform team) |

### Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Registration (POST /beneficiary) | 100 requests/min |
| Read endpoints (GET) | 300 requests/min |
| Analytics endpoints | 60 requests/min |

---

## 🗄️ Database Access Rules

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHARED NEON PostgreSQL                         │
│                                                                   │
│  Dev A (Layer 1)          Platform (Layer 2)     Dev B (Tracking) │
│  ──────────────          ────────────────────    ──────────────── │
│  ❌ NO direct DB         ✅ Full read/write     ❌ NO direct DB  │
│     access                  access                  access        │
│                                                                   │
│  ✅ Access via            ✅ Owns the schema     ✅ Access via    │
│     REST APIs only           and migrations         REST APIs    │
│                                                     only         │
└─────────────────────────────────────────────────────────────────┘
```

> **IMPORTANT:** Only the Platform Layer has direct database access. Dev A and Dev B MUST use the REST APIs to read/write data. This ensures data integrity, validation, and consistent behavior.

**Exception:** If Dev B needs a direct DB connection for performance-critical queries (e.g., complex analytics), we can set up a **read-only replica connection string**. Discuss with the platform team first.

---

## 🧪 Testing Your Integration

### Step 1: Set up locally

```bash
# Clone the repo
git clone <repo-url>
cd vaani/backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Fill in your Neon DATABASE_URL

# Start the server
npm run dev
# Server runs on http://localhost:3001
```

### Step 2: Test with cURL

```bash
# Health check
curl http://localhost:3001/health

# Register a test beneficiary
curl -X POST http://localhost:3001/api/v1/beneficiary/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vanisetu-layer1-secret-key-2025" \
  -d '{
    "beneficiary": {
      "name": "Test User",
      "phone": "+91-9999999999",
      "district": "Ranchi",
      "state": "Jharkhand"
    },
    "skills_extracted": [],
    "call_id": "TEST-001",
    "language_detected": "hi"
  }'
```

### Step 3: Verify in Neon Dashboard

Go to your Neon console → SQL Editor → `SELECT * FROM beneficiaries;`

---

## 📞 Contact

| Person | Owns | Communication |
|--------|------|--------------|
| Platform Developer | Backend APIs, Database, Dashboard | Slack: #platform-layer |
| Developer A | Voice AI, STT/TTS, Conversation Engine | Slack: #ai-agent-layer |
| Developer B | Recommendation Engine, Tracking, SMS | Slack: #tracking-layer |

> **When in doubt, check the API first.** If the endpoint doesn't exist yet, create a GitHub issue tagged `platform-layer` and we'll build it.
