import { z } from 'zod';

/**
 * Zod schema for creating an enrollment
 */
export const createEnrollmentSchema = z.object({
  beneficiary_id: z.string().uuid(),
  program_id: z.string().uuid(),
  match_score: z.number().min(0).max(1).optional(),
});

/**
 * Zod schema for updating enrollment status
 */
export const updateEnrollmentStatusSchema = z.object({
  status: z.enum(['enrolled', 'attending', 'completed', 'dropped', 'certified']),
  certificate_id: z.string().max(100).optional(),
});

/**
 * Zod schema for marking attendance
 */
export const markAttendanceSchema = z.object({
  enrollment_id: z.string().uuid(),
  date: z.string(), // ISO date string YYYY-MM-DD
  is_present: z.boolean(),
  marked_by: z.string().max(100).optional(),
});

/**
 * Zod schema for batch attendance (multiple students at once)
 */
export const batchAttendanceSchema = z.object({
  program_id: z.string().uuid(),
  date: z.string(),
  records: z.array(z.object({
    enrollment_id: z.string().uuid(),
    is_present: z.boolean(),
  })).min(1),
  marked_by: z.string().max(100).optional(),
});

/**
 * Zod schema for follow-ups
 */
export const createFollowupSchema = z.object({
  beneficiary_id: z.string().uuid(),
  followup_type: z.enum(['sms', 'call', 'whatsapp']),
  scheduled_at: z.string(), // ISO datetime string
  purpose: z.string().max(200).optional(),
});

/**
 * Zod schema for posting outcomes
 */
export const createOutcomeSchema = z.object({
  beneficiary_id: z.string().uuid(),
  enrollment_id: z.string().uuid().optional(),
  check_date: z.string().optional(),
  income_before: z.number().int().min(0).optional(),
  income_after: z.number().int().min(0).optional(),
  employment_status: z.enum(['employed', 'self_employed', 'unemployed', 'same']).optional(),
  is_using_skill: z.boolean().optional(),
  satisfaction: z.number().int().min(1).max(5).optional(),
  notes: z.string().optional(),
  data_source: z.enum(['ai_call', 'sms', 'field_worker', 'training_center']).optional(),
});
