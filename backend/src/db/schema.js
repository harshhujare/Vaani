import {
  pgTable, uuid, varchar, integer, boolean,
  timestamp, text, real, date, pgEnum
} from 'drizzle-orm/pg-core';

// ══════════════════════════════════════════
// ENUMS
// ══════════════════════════════════════════

export const beneficiaryStatusEnum = pgEnum('beneficiary_status', [
  'registered', 'assessed', 'enrolled',
  'attending', 'dropped', 'completed',
  'certified', 'employed'
]);

export const enrollmentStatusEnum = pgEnum('enrollment_status', [
  'enrolled', 'attending', 'completed', 'dropped', 'certified'
]);

export const userRoleEnum = pgEnum('user_role', [
  'admin', 'district_officer', 'state_officer', 'training_center', 'viewer'
]);

// ══════════════════════════════════════════
// 1. BENEFICIARIES
// ══════════════════════════════════════════

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
  status:          beneficiaryStatusEnum('status').default('registered'),
  createdAt:       timestamp('created_at').defaultNow(),
  updatedAt:       timestamp('updated_at').defaultNow(),
});

// ══════════════════════════════════════════
// 2. BENEFICIARY SKILLS
// ══════════════════════════════════════════

export const beneficiarySkills = pgTable('beneficiary_skills', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id, { onDelete: 'cascade' }),
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

// ══════════════════════════════════════════
// 3. TRAINING PROGRAMS
// ══════════════════════════════════════════

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

// ══════════════════════════════════════════
// 4. ENROLLMENTS
// ══════════════════════════════════════════

export const enrollments = pgTable('enrollments', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id, { onDelete: 'cascade' }),
  programId:       uuid('program_id').references(() => trainingPrograms.id, { onDelete: 'cascade' }),
  status:          enrollmentStatusEnum('status').default('enrolled'),
  enrolledAt:      timestamp('enrolled_at').defaultNow(),
  startedAt:       timestamp('started_at'),
  completedAt:     timestamp('completed_at'),
  certificateId:   varchar('certificate_id', { length: 100 }),
  matchScore:      real('match_score'),
});

// ══════════════════════════════════════════
// 5. CALL LOGS
// ══════════════════════════════════════════

export const callLogs = pgTable('call_logs', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id, { onDelete: 'cascade' }),
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
// 6. ATTENDANCE (Training center fills daily)
// ══════════════════════════════════════════

export const attendance = pgTable('attendance', {
  id:              uuid('id').primaryKey().defaultRandom(),
  enrollmentId:    uuid('enrollment_id').references(() => enrollments.id, { onDelete: 'cascade' }),
  date:            date('date').notNull(),
  isPresent:       boolean('is_present').default(false),
  markedBy:        varchar('marked_by', { length: 100 }),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ══════════════════════════════════════════
// 7. FOLLOW-UPS
// ══════════════════════════════════════════

export const followups = pgTable('followups', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id, { onDelete: 'cascade' }),
  followupType:    varchar('followup_type', { length: 20 }),
  scheduledAt:     timestamp('scheduled_at').notNull(),
  executedAt:      timestamp('executed_at'),
  status:          varchar('status', { length: 20 }).default('pending'),
  purpose:         varchar('purpose', { length: 200 }),
  responseSummary: text('response_summary'),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ══════════════════════════════════════════
// 8. OUTCOMES
// ══════════════════════════════════════════

export const outcomes = pgTable('outcomes', {
  id:              uuid('id').primaryKey().defaultRandom(),
  beneficiaryId:   uuid('beneficiary_id').references(() => beneficiaries.id, { onDelete: 'cascade' }),
  enrollmentId:    uuid('enrollment_id').references(() => enrollments.id),
  checkDate:       date('check_date'),
  incomeBefore:    integer('income_before'),
  incomeAfter:     integer('income_after'),
  employmentStatus: varchar('employment_status', { length: 50 }),
  isUsingSkill:    boolean('is_using_skill'),
  satisfaction:    integer('satisfaction'),
  notes:           text('notes'),
  dataSource:      varchar('data_source', { length: 20 }),
  createdAt:       timestamp('created_at').defaultNow(),
});

// ══════════════════════════════════════════
// 9. NSQF TAXONOMY (reference/seed data)
// ══════════════════════════════════════════

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

// ══════════════════════════════════════════
// 10. USERS (for auth)
// ══════════════════════════════════════════

export const users = pgTable('users', {
  id:              uuid('id').primaryKey().defaultRandom(),
  email:           varchar('email', { length: 100 }).unique().notNull(),
  passwordHash:    varchar('password_hash', { length: 200 }).notNull(),
  name:            varchar('name', { length: 100 }).notNull(),
  role:            userRoleEnum('role').default('viewer'),
  district:        varchar('district', { length: 100 }),
  state:           varchar('state', { length: 100 }),
  isActive:        boolean('is_active').default(true),
  createdAt:       timestamp('created_at').defaultNow(),
});
