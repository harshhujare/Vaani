import { db } from '../config/db.js';
import { enrollments, trainingPrograms, beneficiaries,
         attendance, followups, outcomes } from '../db/schema.js';
import { eq, and, sql, count } from 'drizzle-orm';
import { sendSuccess, sendCreated, sendError } from '../utils/apiResponse.js';
import { getPagination, getPaginationMeta } from '../utils/pagination.js';

// ═══════════════════════════════════════
// ENROLLMENTS
// ═══════════════════════════════════════

/**
 * POST /api/v1/enrollments
 * Enroll beneficiary in a training program
 */
export const createEnrollment = async (req, res, next) => {
  try {
    const { beneficiary_id, program_id, match_score } = req.body;

    // Verify program exists and has capacity
    const [program] = await db.select()
      .from(trainingPrograms)
      .where(eq(trainingPrograms.id, program_id))
      .limit(1);

    if (!program) {
      return sendError(res, 'Training program not found', 404);
    }

    if (program.capacity && program.enrolledCount >= program.capacity) {
      return sendError(res, 'Training program is full', 400);
    }

    // Create enrollment
    const [enrollment] = await db.insert(enrollments).values({
      beneficiaryId: beneficiary_id,
      programId: program_id,
      matchScore: match_score,
    }).returning();

    // Increment enrolled count
    await db.update(trainingPrograms)
      .set({ enrolledCount: sql`${trainingPrograms.enrolledCount} + 1` })
      .where(eq(trainingPrograms.id, program_id));

    // Update beneficiary status to 'enrolled'
    await db.update(beneficiaries)
      .set({ status: 'enrolled', updatedAt: new Date() })
      .where(eq(beneficiaries.id, beneficiary_id));

    return sendCreated(res, enrollment, 'Beneficiary enrolled successfully');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/enrollments
 * List enrollments with filters
 */
export const listEnrollments = async (req, res, next) => {
  try {
    const { page, limit, offset } = getPagination(req.query);
    const { status, program_id, beneficiary_id } = req.query;

    const conditions = [];
    if (status) conditions.push(eq(enrollments.status, status));
    if (program_id) conditions.push(eq(enrollments.programId, program_id));
    if (beneficiary_id) conditions.push(eq(enrollments.beneficiaryId, beneficiary_id));

    const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

    const [{ value: total }] = await db.select({ value: count() })
      .from(enrollments)
      .where(whereClause);

    const results = await db.select()
      .from(enrollments)
      .where(whereClause)
      .orderBy(enrollments.enrolledAt)
      .limit(limit)
      .offset(offset);

    return sendSuccess(res, results, 'Enrollments fetched', 200,
      getPaginationMeta(page, limit, Number(total)));

  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/v1/enrollments/:id/status
 * Update enrollment status (e.g., enrolled → attending → completed)
 */
export const updateEnrollmentStatus = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status, certificate_id } = req.body;

    const updateData = { status };
    if (status === 'attending') updateData.startedAt = new Date();
    if (status === 'completed') updateData.completedAt = new Date();
    if (certificate_id) updateData.certificateId = certificate_id;

    const [updated] = await db.update(enrollments)
      .set(updateData)
      .where(eq(enrollments.id, id))
      .returning();

    if (!updated) {
      return sendError(res, 'Enrollment not found', 404);
    }

    // Sync beneficiary status
    const statusMap = {
      'attending': 'attending',
      'completed': 'completed',
      'dropped': 'dropped',
      'certified': 'certified',
    };
    if (statusMap[status]) {
      await db.update(beneficiaries)
        .set({ status: statusMap[status], updatedAt: new Date() })
        .where(eq(beneficiaries.id, updated.beneficiaryId));
    }

    return sendSuccess(res, updated, `Enrollment status updated to '${status}'`);

  } catch (error) {
    next(error);
  }
};

// ═══════════════════════════════════════
// ATTENDANCE
// ═══════════════════════════════════════

/**
 * POST /api/v1/attendance
 * Mark single attendance record
 */
export const markAttendance = async (req, res, next) => {
  try {
    const { enrollment_id, date, is_present, marked_by } = req.body;

    const [record] = await db.insert(attendance).values({
      enrollmentId: enrollment_id,
      date,
      isPresent: is_present,
      markedBy: marked_by,
    }).returning();

    return sendCreated(res, record, 'Attendance marked');

  } catch (error) {
    next(error);
  }
};

/**
 * POST /api/v1/attendance/batch
 * Mark attendance for entire batch at once (training center submits this)
 */
export const markBatchAttendance = async (req, res, next) => {
  try {
    const { program_id, date, records, marked_by } = req.body;

    const attendanceRecords = records.map((r) => ({
      enrollmentId: r.enrollment_id,
      date,
      isPresent: r.is_present,
      markedBy: marked_by,
    }));

    const inserted = await db.insert(attendance)
      .values(attendanceRecords)
      .returning();

    return sendCreated(res, {
      program_id,
      date,
      total_marked: inserted.length,
      present: inserted.filter(r => r.isPresent).length,
      absent: inserted.filter(r => !r.isPresent).length,
    }, 'Batch attendance marked');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/attendance/:enrollmentId
 * Get attendance history for an enrollment
 */
export const getAttendanceHistory = async (req, res, next) => {
  try {
    const { enrollmentId } = req.params;

    const records = await db.select()
      .from(attendance)
      .where(eq(attendance.enrollmentId, enrollmentId))
      .orderBy(attendance.date);

    const total = records.length;
    const present = records.filter(r => r.isPresent).length;

    return sendSuccess(res, {
      records,
      summary: {
        total_days: total,
        present,
        absent: total - present,
        attendance_rate: total > 0 ? ((present / total) * 100).toFixed(1) : 0,
      }
    }, 'Attendance history fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/attendance/at-risk
 * Get students with 5+ consecutive absent days (for Dev B dropout detection)
 */
export const getAtRiskStudents = async (req, res, next) => {
  try {
    const absentDays = parseInt(req.query.absent_days) || 5;

    // Get enrollments with recent consecutive absences
    const result = await db.execute(sql`
      WITH recent_attendance AS (
        SELECT
          a.enrollment_id,
          a.date,
          a.is_present,
          ROW_NUMBER() OVER (PARTITION BY a.enrollment_id ORDER BY a.date DESC) as rn
        FROM attendance a
        WHERE a.is_present = false
      ),
      consecutive_absences AS (
        SELECT
          enrollment_id,
          COUNT(*) as absent_count,
          MIN(date) as absent_since
        FROM recent_attendance
        WHERE rn <= ${absentDays}
        GROUP BY enrollment_id
        HAVING COUNT(*) >= ${absentDays}
      )
      SELECT
        ca.enrollment_id,
        ca.absent_count as consecutive_absent_days,
        ca.absent_since,
        b.id as beneficiary_id,
        b.name,
        b.phone,
        tp.name as program_name
      FROM consecutive_absences ca
      JOIN enrollments e ON e.id = ca.enrollment_id
      JOIN beneficiaries b ON b.id = e.beneficiary_id
      JOIN training_programs tp ON tp.id = e.program_id
      WHERE e.status = 'attending'
    `);

    return sendSuccess(res, result.rows || [], 'At-risk students fetched');

  } catch (error) {
    next(error);
  }
};

// ═══════════════════════════════════════
// FOLLOW-UPS (Dev B integration)
// ═══════════════════════════════════════

/**
 * POST /api/v1/followups
 */
export const createFollowup = async (req, res, next) => {
  try {
    const { beneficiary_id, followup_type, scheduled_at, purpose } = req.body;

    const [followup] = await db.insert(followups).values({
      beneficiaryId: beneficiary_id,
      followupType: followup_type,
      scheduledAt: new Date(scheduled_at),
      purpose,
    }).returning();

    return sendCreated(res, followup, 'Follow-up scheduled');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/followups/pending
 */
export const getPendingFollowups = async (req, res, next) => {
  try {
    const result = await db.select({
      id: followups.id,
      beneficiaryId: followups.beneficiaryId,
      phone: beneficiaries.phone,
      followupType: followups.followupType,
      scheduledAt: followups.scheduledAt,
      purpose: followups.purpose,
      language: beneficiaries.language,
    })
      .from(followups)
      .innerJoin(beneficiaries, eq(followups.beneficiaryId, beneficiaries.id))
      .where(
        and(
          eq(followups.status, 'pending'),
          sql`${followups.scheduledAt} <= NOW()`
        )
      )
      .orderBy(followups.scheduledAt);

    return sendSuccess(res, result, 'Pending follow-ups fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * PATCH /api/v1/followups/:id
 */
export const updateFollowup = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { status, executed_at, response_summary } = req.body;

    const [updated] = await db.update(followups)
      .set({
        status,
        executedAt: executed_at ? new Date(executed_at) : new Date(),
        responseSummary: response_summary,
      })
      .where(eq(followups.id, id))
      .returning();

    if (!updated) {
      return sendError(res, 'Follow-up not found', 404);
    }

    return sendSuccess(res, updated, 'Follow-up updated');

  } catch (error) {
    next(error);
  }
};

// ═══════════════════════════════════════
// OUTCOMES (Dev B integration)
// ═══════════════════════════════════════

/**
 * POST /api/v1/outcomes
 */
export const createOutcome = async (req, res, next) => {
  try {
    const data = req.body;

    const [outcome] = await db.insert(outcomes).values({
      beneficiaryId: data.beneficiary_id,
      enrollmentId: data.enrollment_id,
      checkDate: data.check_date,
      incomeBefore: data.income_before,
      incomeAfter: data.income_after,
      employmentStatus: data.employment_status,
      isUsingSkill: data.is_using_skill,
      satisfaction: data.satisfaction,
      notes: data.notes,
      dataSource: data.data_source,
    }).returning();

    return sendCreated(res, outcome, 'Outcome recorded');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/outcomes/:beneficiaryId
 */
export const getOutcomes = async (req, res, next) => {
  try {
    const { beneficiaryId } = req.params;

    const result = await db.select()
      .from(outcomes)
      .where(eq(outcomes.beneficiaryId, beneficiaryId))
      .orderBy(outcomes.checkDate);

    return sendSuccess(res, result, 'Outcomes fetched');

  } catch (error) {
    next(error);
  }
};
