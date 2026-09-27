import { db } from '../config/db.js';
import { beneficiaries, beneficiarySkills, callLogs } from '../db/schema.js';
import { eq, ilike, and, sql, count } from 'drizzle-orm';
import { sendSuccess, sendCreated, sendError } from '../utils/apiResponse.js';
import { getPagination, getPaginationMeta } from '../utils/pagination.js';
import { ApiError } from '../middleware/errorHandler.js';

/**
 * POST /api/v1/beneficiary/register
 * Called by Layer 1 after every completed voice call
 */
export const registerBeneficiary = async (req, res, next) => {
  try {
    const { beneficiary, skills_extracted, call_id, call_duration_seconds,
            language_detected, nsqf_assessment, conversation_transcript,
            ai_confidence_overall } = req.body;

    // Check if phone already exists
    const existing = await db.select({ id: beneficiaries.id })
      .from(beneficiaries)
      .where(eq(beneficiaries.phone, beneficiary.phone))
      .limit(1);

    if (existing.length > 0) {
      return sendError(res, 'Beneficiary with this phone already exists. Use PUT to update.', 409, null);
    }

    // Insert beneficiary
    const [newBeneficiary] = await db.insert(beneficiaries).values({
      phone: beneficiary.phone,
      name: beneficiary.name,
      age: beneficiary.age,
      gender: beneficiary.gender,
      district: beneficiary.district,
      state: beneficiary.state,
      village: beneficiary.village,
      casteCategory: beneficiary.caste_category,
      educationLevel: beneficiary.education_level,
      monthlyIncome: beneficiary.current_monthly_income,
      householdSize: beneficiary.household_size,
      bplStatus: beneficiary.bpl_status,
      language: language_detected,
    }).returning();

    // Insert skills
    let skillsSaved = 0;
    if (skills_extracted && skills_extracted.length > 0) {
      const skillRecords = skills_extracted.map((skill) => ({
        beneficiaryId: newBeneficiary.id,
        skillName: skill.skill_name,
        sector: skill.sector,
        subSector: skill.sub_sector,
        experienceYears: skill.experience_years,
        isPrimary: skill.is_primary,
        nsqfLevel: skill.nsqf_level_mapped,
        confidenceScore: skill.confidence_score,
        subSkills: skill.sub_skills,
      }));

      await db.insert(beneficiarySkills).values(skillRecords);
      skillsSaved = skillRecords.length;
    }

    // Insert call log
    let callLogId = null;
    if (call_id) {
      const [log] = await db.insert(callLogs).values({
        beneficiaryId: newBeneficiary.id,
        callId: call_id,
        callType: 'inbound',
        durationSeconds: call_duration_seconds,
        language: language_detected,
        transcript: conversation_transcript,
        aiConfidence: ai_confidence_overall,
      }).returning();
      callLogId = log.id;
    }

    return sendCreated(res, {
      beneficiary_id: newBeneficiary.id,
      status: newBeneficiary.status,
      skills_saved: skillsSaved,
      call_log_id: callLogId,
    }, 'Beneficiary registered successfully');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/beneficiaries
 * List all beneficiaries with pagination and filters
 */
export const listBeneficiaries = async (req, res, next) => {
  try {
    const { page, limit, offset } = getPagination(req.query);
    const { district, state, status, search } = req.query;

    // Build filter conditions
    const conditions = [];
    if (district) conditions.push(ilike(beneficiaries.district, `%${district}%`));
    if (state) conditions.push(ilike(beneficiaries.state, `%${state}%`));
    if (status) conditions.push(eq(beneficiaries.status, status));
    if (search) {
      conditions.push(
        sql`(${beneficiaries.name} ILIKE ${`%${search}%`} OR ${beneficiaries.phone} ILIKE ${`%${search}%`})`
      );
    }

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

    // Get total count
    const [{ value: total }] = await db.select({ value: count() })
      .from(beneficiaries)
      .where(whereClause);

    // Get paginated results
    const results = await db.select()
      .from(beneficiaries)
      .where(whereClause)
      .orderBy(beneficiaries.createdAt)
      .limit(limit)
      .offset(offset);

    return sendSuccess(res, results, 'Beneficiaries fetched', 200,
      getPaginationMeta(page, limit, Number(total)));

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/beneficiary/:id
 * Get full beneficiary profile with skills
 */
export const getBeneficiary = async (req, res, next) => {
  try {
    const { id } = req.params;

    const [beneficiary] = await db.select()
      .from(beneficiaries)
      .where(eq(beneficiaries.id, id))
      .limit(1);

    if (!beneficiary) {
      return sendError(res, 'Beneficiary not found', 404);
    }

    // Get skills
    const skills = await db.select()
      .from(beneficiarySkills)
      .where(eq(beneficiarySkills.beneficiaryId, id));

    return sendSuccess(res, { ...beneficiary, skills }, 'Beneficiary fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * PUT /api/v1/beneficiary/:id
 * Update beneficiary profile
 */
export const updateBeneficiary = async (req, res, next) => {
  try {
    const { id } = req.params;

    const [updated] = await db.update(beneficiaries)
      .set({ ...req.body, updatedAt: new Date() })
      .where(eq(beneficiaries.id, id))
      .returning();

    if (!updated) {
      return sendError(res, 'Beneficiary not found', 404);
    }

    return sendSuccess(res, updated, 'Beneficiary updated');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/beneficiary/:id/skills
 * Get skills for a beneficiary
 */
export const getBeneficiarySkills = async (req, res, next) => {
  try {
    const { id } = req.params;

    const skills = await db.select()
      .from(beneficiarySkills)
      .where(eq(beneficiarySkills.beneficiaryId, id));

    return sendSuccess(res, skills, 'Skills fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/v1/beneficiary/:id/status
 * Update beneficiary lifecycle status
 */
export const updateBeneficiaryStatus = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    const [updated] = await db.update(beneficiaries)
      .set({ status, updatedAt: new Date() })
      .where(eq(beneficiaries.id, id))
      .returning();

    if (!updated) {
      return sendError(res, 'Beneficiary not found', 404);
    }

    return sendSuccess(res, updated, `Status updated to '${status}'`);

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/beneficiary/phone/:phone
 * Check if phone exists (for Layer 1 deduplication)
 */
export const checkPhone = async (req, res, next) => {
  try {
    const { phone } = req.params;

    const [existing] = await db.select({
      id: beneficiaries.id,
      name: beneficiaries.name,
      status: beneficiaries.status,
    })
      .from(beneficiaries)
      .where(eq(beneficiaries.phone, phone))
      .limit(1);

    if (existing) {
      return sendSuccess(res, { exists: true, ...existing }, 'Phone found');
    }

    return sendSuccess(res, { exists: false }, 'Phone not found');

  } catch (error) {
    next(error);
  }
};
