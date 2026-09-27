# 📋 Platform Layer — Documents Created

## Two files created for review:

---

### 1. 📄 Implementation Plan
**File:** [platform_layer_plan.md](file:///c:/Documents/Vaani/Document/platform_layer_plan.md)

Your personal roadmap — **14 days across 3 phases:**

| Phase | Days | What You Build |
|-------|------|---------------|
| **Phase 1 — Foundation** | Days 1-5 | Express server, Neon DB + Drizzle schema, all CRUD APIs (beneficiary, programs, enrollment, attendance, call logs) |
| **Phase 2 — Business Logic** | Days 6-9 | JWT auth + RBAC, analytics endpoints, integration endpoints for Dev B, API documentation |
| **Phase 3 — Frontend** | Days 10-14 | React dashboard (login, dashboard home, beneficiary pages, programs, training center portal, analytics) |

**Key contents:**
- Complete project folder structure (`backend/` + `frontend/` + `docs/`)
- Day-by-day checklist with `- [ ]` checkboxes
- All npm packages listed (backend + frontend)
- `.env.example` with all required variables
- Standard API response format
- Phase dependency diagram

> [!IMPORTANT]
> **Dev A and Dev B can start integrating after Day 3** (beneficiary register endpoint is live). They don't need to wait for the full platform.

---

### 2. 📄 Integration Guide (For Other Developers)
**File:** [INTEGRATION_GUIDE.md](file:///c:/Documents/Vaani/Document/INTEGRATION_GUIDE.md)

Documentation that other developers use to connect their modules:

#### For Developer A (AI Agent Layer — Python):
| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `POST /beneficiary/register` | Send extracted data after every voice call |
| 2 | `PUT /beneficiary/:id` | Update when beneficiary calls again |
| 3 | `POST /call-logs` | Log every call (even failed ones) |
| 4 | `GET /taxonomy` | Fetch NSQF skill keywords for mapping |
| 5 | `GET /beneficiary/phone/:phone` | Check if phone already exists |

#### For Developer B (Recommendation Engine):
| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `GET /recommend/data/:id` | Get beneficiary + available programs data |
| 2 | `POST /recommend/result` | Post ranked recommendation results back |
| 3 | `GET /programs?filters` | Query programs by sector, NSQF, district |
| 4 | `GET /taxonomy` | Reference skill taxonomy |

#### For Developer B (Tracking System):
| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `POST /followups` | Schedule follow-up SMS/calls |
| 2 | `GET /followups/pending` | Poll for pending tasks (every 15 min) |
| 3 | `PATCH /followups/:id` | Report execution result |
| 4 | `POST /outcomes` | Submit outcome data (income change, employment) |
| 5 | `GET /attendance/at-risk` | Get students absent 5+ days |
| 6 | `PATCH /beneficiary/:id/status` | Update lifecycle status |

**Also includes:**
- Authentication method (API keys for server-to-server)
- Complete JSON request/response examples for every endpoint
- Error codes and rate limits
- Database access rules (only Platform has direct DB access)
- cURL examples for testing
- Recommendation scoring algorithm reference

---

## 🏛️ Architecture Summary

```
Dev A (Python)                    YOU (Node.js)                  Dev B (Node.js)
─────────────                    ──────────────                 ────────────────
Telephony                        Express Server                 Recommendation
STT/TTS (Bhashini)     ──API──► Neon PostgreSQL  ◄──API──     Engine
Conversation AI                  Drizzle ORM                    node-cron
NLP / Entity Extract             React Dashboard                SMS (MSG91)
                                 JWT Auth                       Outcome Tracking
```

> [!TIP]
> **All communication is via REST APIs.** Dev A and Dev B never touch the database directly. You own the data layer.

---

## ✏️ Review Checklist

Before approving, consider:
- [ ] Does the 14-day timeline feel realistic?
- [ ] Are there any APIs missing that Dev A or Dev B would need?
- [ ] Should we adjust which developer owns the Recommendation Engine endpoints?
- [ ] Do you want me to start building the actual code (Day 1: Express + Neon setup)?
