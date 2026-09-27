import { db } from '../config/db.js';
import { beneficiaries, beneficiarySkills, enrollments,
         trainingPrograms, attendance, outcomes } from '../db/schema.js';
import { eq, sql, count } from 'drizzle-orm';
import { sendSuccess } from '../utils/apiResponse.js';

/**
 * GET /api/v1/analytics/dashboard
 * Aggregate stats for the dashboard home page
 */
export const getDashboardStats = async (req, res, next) => {
  try {
    // Total beneficiaries
    const [{ value: totalBeneficiaries }] = await db.select({ value: count() })
      .from(beneficiaries);

    // Total skills mapped
    const [{ value: totalSkills }] = await db.select({ value: count() })
      .from(beneficiarySkills);

    // Total enrolled
    const [{ value: totalEnrolled }] = await db.select({ value: count() })
      .from(enrollments);

    // Completed
    const [{ value: totalCompleted }] = await db.select({ value: count() })
      .from(enrollments)
      .where(eq(enrollments.status, 'completed'));

    // Certified
    const [{ value: totalCertified }] = await db.select({ value: count() })
      .from(enrollments)
      .where(eq(enrollments.status, 'certified'));

    // Active programs
    const [{ value: activePrograms }] = await db.select({ value: count() })
      .from(trainingPrograms)
      .where(eq(trainingPrograms.isActive, true));

    // Status breakdown
    const statusBreakdown = await db.select({
      status: beneficiaries.status,
      count: count(),
    })
      .from(beneficiaries)
      .groupBy(beneficiaries.status);

    // Average income change from outcomes
    const avgIncomeResult = await db.execute(sql`
      SELECT
        COALESCE(AVG(income_after - income_before), 0) as avg_income_change
      FROM outcomes
      WHERE income_before IS NOT NULL AND income_after IS NOT NULL
    `);
    const avgIncomeChange = Math.round(avgIncomeResult.rows?.[0]?.avg_income_change || 0);

    // Overall attendance rate
    const attendanceResult = await db.execute(sql`
      SELECT
        COUNT(*) FILTER (WHERE is_present = true) as present,
        COUNT(*) as total
      FROM attendance
    `);
    const row = attendanceResult.rows?.[0];
    const attendanceRate = row?.total > 0
      ? ((row.present / row.total) * 100).toFixed(1)
      : 0;

    return sendSuccess(res, {
      totalBeneficiaries: Number(totalBeneficiaries),
      totalSkillsMapped: Number(totalSkills),
      totalEnrolled: Number(totalEnrolled),
      totalCompleted: Number(totalCompleted),
      totalCertified: Number(totalCertified),
      activePrograms: Number(activePrograms),
      avgIncomeChange,
      attendanceRate: Number(attendanceRate),
      statusBreakdown: statusBreakdown.reduce((acc, s) => {
        acc[s.status] = Number(s.count);
        return acc;
      }, {}),
    }, 'Dashboard stats fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/analytics/funnel
 * Conversion funnel data
 */
export const getFunnel = async (req, res, next) => {
  try {
    const stages = ['registered', 'assessed', 'enrolled', 'attending',
                    'completed', 'certified', 'employed'];

    const statusCounts = await db.select({
      status: beneficiaries.status,
      count: count(),
    })
      .from(beneficiaries)
      .groupBy(beneficiaries.status);

    const countMap = statusCounts.reduce((acc, s) => {
      acc[s.status] = Number(s.count);
      return acc;
    }, {});

    // Build cumulative funnel (each stage includes all stages after it)
    let cumulative = 0;
    const funnel = stages.reverse().map((stage) => {
      cumulative += (countMap[stage] || 0);
      return { stage, count: cumulative };
    }).reverse();

    // Also count dropped separately
    const dropped = countMap['dropped'] || 0;

    return sendSuccess(res, { funnel, dropped }, 'Funnel data fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/analytics/district/:name
 * Per-district breakdown
 */
export const getDistrictStats = async (req, res, next) => {
  try {
    const { name } = req.params;

    const stats = await db.execute(sql`
      SELECT
        COUNT(*) as total_beneficiaries,
        COUNT(*) FILTER (WHERE status = 'enrolled' OR status = 'attending' OR
                         status = 'completed' OR status = 'certified' OR
                         status = 'employed') as total_enrolled,
        COUNT(*) FILTER (WHERE status = 'completed' OR status = 'certified' OR
                         status = 'employed') as total_completed
      FROM beneficiaries
      WHERE LOWER(district) = LOWER(${name})
    `);

    const programs = await db.select()
      .from(trainingPrograms)
      .where(sql`LOWER(${trainingPrograms.district}) = LOWER(${name})`);

    const topSkills = await db.execute(sql`
      SELECT bs.sector, bs.skill_name, COUNT(*) as count
      FROM beneficiary_skills bs
      JOIN beneficiaries b ON b.id = bs.beneficiary_id
      WHERE LOWER(b.district) = LOWER(${name})
      GROUP BY bs.sector, bs.skill_name
      ORDER BY count DESC
      LIMIT 10
    `);

    return sendSuccess(res, {
      district: name,
      stats: stats.rows?.[0] || {},
      programs,
      topSkills: topSkills.rows || [],
    }, 'District stats fetched');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/analytics/skills-heatmap
 * Skill distribution across districts
 */
export const getSkillsHeatmap = async (req, res, next) => {
  try {
    const result = await db.execute(sql`
      SELECT
        b.district,
        bs.sector,
        COUNT(*) as count
      FROM beneficiary_skills bs
      JOIN beneficiaries b ON b.id = bs.beneficiary_id
      WHERE b.district IS NOT NULL
      GROUP BY b.district, bs.sector
      ORDER BY count DESC
    `);

    return sendSuccess(res, result.rows || [], 'Skills heatmap fetched');

  } catch (error) {
    next(error);
  }
};
