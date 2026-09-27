import { z } from 'zod';

/**
 * Zod schema for beneficiary registration (from Layer 1)
 */
export const registerBeneficiarySchema = z.object({
  call_id: z.string().min(1),
  call_duration_seconds: z.number().int().positive().optional(),
  language_detected: z.string().max(10).optional(),

  beneficiary: z.object({
    name: z.string().min(1).max(100),
    phone: z.string().min(10).max(15),
    age: z.number().int().min(1).max(120).optional(),
    gender: z.enum(['male', 'female', 'other']).optional(),
    district: z.string().max(100).optional(),
    state: z.string().max(100).optional(),
    village: z.string().max(200).optional(),
    caste_category: z.enum(['SC', 'ST', 'OBC', 'General']).optional().default('SC'),
    education_level: z.string().max(50).optional(),
    current_monthly_income: z.number().int().min(0).optional(),
    household_size: z.number().int().min(1).optional(),
    bpl_status: z.boolean().optional().default(true),
  }),

  skills_extracted: z.array(z.object({
    skill_name: z.string().min(1).max(200),
    sector: z.string().max(100).optional(),
    sub_sector: z.string().max(100).optional(),
    experience_years: z.number().int().min(0).optional(),
    is_primary: z.boolean().optional().default(false),
    confidence_score: z.number().min(0).max(1).optional(),
    nsqf_level_mapped: z.number().int().min(1).max(8).optional(),
    sub_skills: z.array(z.string()).optional().default([]),
  })).optional().default([]),

  nsqf_assessment: z.object({
    primary_nsqf_level: z.number().int().min(1).max(8).optional(),
    assessment_basis: z.string().optional(),
    recommended_training_level: z.number().int().min(1).max(8).optional(),
    recommended_sector: z.string().optional(),
  }).optional(),

  training_preference: z.object({
    willing_to_train: z.boolean().optional(),
    preferred_timing: z.string().optional(),
    max_travel_distance_km: z.number().optional(),
    preferred_language: z.string().optional(),
  }).optional(),

  conversation_transcript: z.string().optional(),
  ai_confidence_overall: z.number().min(0).max(1).optional(),
});

/**
 * Zod schema for updating a beneficiary
 */
export const updateBeneficiarySchema = z.object({
  name: z.string().min(1).max(100).optional(),
  age: z.number().int().min(1).max(120).optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  district: z.string().max(100).optional(),
  state: z.string().max(100).optional(),
  village: z.string().max(200).optional(),
  casteCategory: z.string().max(10).optional(),
  educationLevel: z.string().max(50).optional(),
  monthlyIncome: z.number().int().min(0).optional(),
  householdSize: z.number().int().min(1).optional(),
  bplStatus: z.boolean().optional(),
  language: z.string().max(10).optional(),
});

/**
 * Zod schema for updating beneficiary status
 */
export const updateStatusSchema = z.object({
  status: z.enum([
    'registered', 'assessed', 'enrolled',
    'attending', 'dropped', 'completed',
    'certified', 'employed'
  ]),
  updated_by: z.string().optional().default('system'),
});
