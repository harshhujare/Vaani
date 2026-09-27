import { Router } from 'express';
import {
  createCallLog, getCallLogs, getTaxonomy
} from '../controllers/program.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import { createCallLogSchema } from '../validators/program.validator.js';

const router = Router();

// Call Logs — Layer 1 sends after each call
router.post('/', authMiddleware, validate(createCallLogSchema), createCallLog);
router.get('/:beneficiaryId', authMiddleware, getCallLogs);

export default router;
