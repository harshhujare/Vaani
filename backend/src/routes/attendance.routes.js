import { Router } from 'express';
import {
  markAttendance, markBatchAttendance, getAttendanceHistory, getAtRiskStudents
} from '../controllers/enrollment.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import { markAttendanceSchema, batchAttendanceSchema } from '../validators/enrollment.validator.js';

const router = Router();

// Single attendance
router.post('/', authMiddleware, validate(markAttendanceSchema), markAttendance);

// Batch attendance (training center submits whole class at once)
router.post('/batch', authMiddleware, validate(batchAttendanceSchema), markBatchAttendance);

// Get attendance history for an enrollment
router.get('/:enrollmentId', authMiddleware, getAttendanceHistory);

// Get at-risk students (Dev B dropout detection)
router.get('/at-risk', authMiddleware, getAtRiskStudents);

export default router;
