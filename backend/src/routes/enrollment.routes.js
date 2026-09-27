import { Router } from 'express';
import {
  createEnrollment, listEnrollments, updateEnrollmentStatus,
  markAttendance, markBatchAttendance, getAttendanceHistory, getAtRiskStudents,
  createFollowup, getPendingFollowups, updateFollowup,
  createOutcome, getOutcomes
} from '../controllers/enrollment.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import {
  createEnrollmentSchema, updateEnrollmentStatusSchema,
  markAttendanceSchema, batchAttendanceSchema,
  createFollowupSchema, createOutcomeSchema
} from '../validators/enrollment.validator.js';

const router = Router();

// ── Enrollments ──
router.post('/', authMiddleware, validate(createEnrollmentSchema), createEnrollment);
router.get('/', authMiddleware, listEnrollments);
router.patch('/:id/status', authMiddleware, validate(updateEnrollmentStatusSchema), updateEnrollmentStatus);

export default router;
