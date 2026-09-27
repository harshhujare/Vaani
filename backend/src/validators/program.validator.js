import { z } from 'zod';

/**
 * Zod schema for creating a training program
 */
export const createProgramSchema = z.object({
  name: z.string().min(1).max(200),
  sector: z.string().max(100).optional(),
  sub_sector: z.string().max(100).optional(),
  nsqf_level: z.number().int().min(1).max(8).optional(),
  duration_days: z.number().int().positive().optional(),
  district: z.string().max(100).optional(),
  state: z.string().max(100).optional(),
  training_center: z.string().max(200).optional(),
  provider: z.string().max(200).optional(),
  capacity: z.number().int().positive().optional(),
  start_date: z.string().optional(), // ISO date string
  end_date: z.string().optional(),
  certification: z.string().max(100).optional(),
  scheme: z.string().max(100).optional().default('PM-AJAY GIA'),
});

/**
 * Zod schema for updating a training program
 */
export const updateProgramSchema = createProgramSchema.partial();

/**
 * Zod schema for creating a call log
 */
export const createCallLogSchema = z.object({
  beneficiary_id: z.string().uuid(),
  call_id: z.string().min(1).max(100),
  call_type: z.enum(['inbound', 'outbound_followup']).optional().default('inbound'),
  duration_seconds: z.number().int().min(0).optional(),
  language: z.string().max(10).optional(),
  transcript: z.string().optional(),
  ai_confidence: z.number().min(0).max(1).optional(),
  raw_audio_url: z.string().max(500).optional(),
});
