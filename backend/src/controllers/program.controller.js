import { db } from '../config/db.js';
import { trainingPrograms, callLogs, nsqfTaxonomy } from '../db/schema.js';
import { eq, ilike, and, sql, count } from 'drizzle-orm';
import { sendSuccess, sendCreated, sendError } from '../utils/apiResponse.js';
import { getPagination, getPaginationMeta } from '../utils/pagination.js';

/**
 * POST /api/v1/programs
 * Create a training program
 */
export const createProgram = async (req, res, next) => {
  try {
    const data = req.body;

    const [program] = await db.insert(trainingPrograms).values({
      name: data.name,
      sector: data.sector,
      subSector: data.sub_sector,
      nsqfLevel: data.nsqf_level,
      durationDays: data.duration_days,
      district: data.district,
      state: data.state,
      trainingCenter: data.training_center,
      provider: data.provider,
      capacity: data.capacity,
      startDate: data.start_date,
      endDate: data.end_date,
      certification: data.certification,
      scheme: data.scheme,
    }).returning();

    return sendCreated(res, program, 'Training program created');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/programs
 * List programs with filters
 */
export const listPrograms = async (req, res, next) => {
  try {
    const { page, limit, offset } = getPagination(req.query);
    const { sector, nsqf_level, district, is_active, search } = req.query;

    const conditions = [];
    if (sector) conditions.push(ilike(trainingPrograms.sector, `%${sector}%`));
    if (nsqf_level) conditions.push(eq(trainingPrograms.nsqfLevel, parseInt(nsqf_level)));
    if (district) conditions.push(ilike(trainingPrograms.district, `%${district}%`));
    if (is_active !== undefined) conditions.push(eq(trainingPrograms.isActive, is_active === 'true'));
    if (search) conditions.push(ilike(trainingPrograms.name, `%${search}%`));

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

    const [{ value: total }] = await db.select({ value: count() })
      .from(trainingPrograms)
      .where(whereClause);

    const results = await db.select()
      .from(trainingPrograms)
      .where(whereClause)
      .orderBy(trainingPrograms.createdAt)
      .limit(limit)
      .offset(offset);

    return sendSuccess(res, results, 'Programs fetched', 200,
      getPaginationMeta(page, limit, Number(total)));

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/programs/:id
 * Get program details
 */
export const getProgram = async (req, res, next) => {
  try {
    const { id } = req.params;

    const [program] = await db.select()
      .from(trainingPrograms)
      .where(eq(trainingPrograms.id, id))
      .limit(1);

    if (!program) {
      return sendError(res, 'Training program not found', 404);
    }

    return sendSuccess(res, program, 'Program fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * PUT /api/v1/programs/:id
 * Update a training program
 */
export const updateProgram = async (req, res, next) => {
  try {
    const { id } = req.params;
    const data = req.body;

    const updateData = {};
    if (data.name !== undefined) updateData.name = data.name;
    if (data.sector !== undefined) updateData.sector = data.sector;
    if (data.sub_sector !== undefined) updateData.subSector = data.sub_sector;
    if (data.nsqf_level !== undefined) updateData.nsqfLevel = data.nsqf_level;
    if (data.duration_days !== undefined) updateData.durationDays = data.duration_days;
    if (data.district !== undefined) updateData.district = data.district;
    if (data.state !== undefined) updateData.state = data.state;
    if (data.training_center !== undefined) updateData.trainingCenter = data.training_center;
    if (data.provider !== undefined) updateData.provider = data.provider;
    if (data.capacity !== undefined) updateData.capacity = data.capacity;
    if (data.start_date !== undefined) updateData.startDate = data.start_date;
    if (data.end_date !== undefined) updateData.endDate = data.end_date;
    if (data.certification !== undefined) updateData.certification = data.certification;
    if (data.is_active !== undefined) updateData.isActive = data.is_active;

    const [updated] = await db.update(trainingPrograms)
      .set(updateData)
      .where(eq(trainingPrograms.id, id))
      .returning();

    if (!updated) {
      return sendError(res, 'Training program not found', 404);
    }

    return sendSuccess(res, updated, 'Program updated');

  } catch (error) {
    next(error);
  }
};

// ═══════════════════════════════════════
// CALL LOGS
// ═══════════════════════════════════════

/**
 * POST /api/v1/call-logs
 * Store call log (Layer 1 sends after each call)
 */
export const createCallLog = async (req, res, next) => {
  try {
    const data = req.body;

    const [log] = await db.insert(callLogs).values({
      beneficiaryId: data.beneficiary_id,
      callId: data.call_id,
      callType: data.call_type,
      durationSeconds: data.duration_seconds,
      language: data.language,
      transcript: data.transcript,
      aiConfidence: data.ai_confidence,
      rawAudioUrl: data.raw_audio_url,
    }).returning();

    return sendCreated(res, log, 'Call log created');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/call-logs/:beneficiaryId
 * Get call history for a beneficiary
 */
export const getCallLogs = async (req, res, next) => {
  try {
    const { beneficiaryId } = req.params;

    const logs = await db.select()
      .from(callLogs)
      .where(eq(callLogs.beneficiaryId, beneficiaryId))
      .orderBy(callLogs.createdAt);

    return sendSuccess(res, logs, 'Call logs fetched');

  } catch (error) {
    next(error);
  }
};

// ═══════════════════════════════════════
// NSQF TAXONOMY
// ═══════════════════════════════════════

/**
 * GET /api/v1/taxonomy
 * Get NSQF skill taxonomy (for Layer 1 skill mapping)
 */
export const getTaxonomy = async (req, res, next) => {
  try {
    const { sector, search } = req.query;

    const conditions = [];
    if (sector) conditions.push(ilike(nsqfTaxonomy.sector, `%${sector}%`));
    if (search) {
      conditions.push(
        sql`(${nsqfTaxonomy.skillName} ILIKE ${`%${search}%`} OR ${nsqfTaxonomy.sector} ILIKE ${`%${search}%`})`
      );
    }

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

    const results = await db.select()
      .from(nsqfTaxonomy)
      .where(whereClause)
      .orderBy(nsqfTaxonomy.sector, nsqfTaxonomy.nsqfLevel);

    return sendSuccess(res, results, 'Taxonomy fetched');

  } catch (error) {
    next(error);
  }
};
