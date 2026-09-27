import { Router } from 'express';
import {
  createProgram, listPrograms, getProgram, updateProgram,
  createCallLog, getCallLogs, getTaxonomy
} from '../controllers/program.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import { createProgramSchema, updateProgramSchema, createCallLogSchema } from '../validators/program.validator.js';

const router = Router();

// Training Programs
router.post('/', authMiddleware, validate(createProgramSchema), createProgram);
router.get('/', authMiddleware, listPrograms);
router.get('/:id', authMiddleware, getProgram);
router.put('/:id', authMiddleware, validate(updateProgramSchema), updateProgram);

export default router;
