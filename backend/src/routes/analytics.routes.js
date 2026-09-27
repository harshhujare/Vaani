import { Router } from 'express';
import {
  getDashboardStats, getFunnel, getDistrictStats, getSkillsHeatmap
} from '../controllers/analytics.controller.js';
import { getTaxonomy } from '../controllers/program.controller.js';
import {
  createFollowup, getPendingFollowups, updateFollowup,
  createOutcome, getOutcomes
} from '../controllers/enrollment.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import { createFollowupSchema, createOutcomeSchema } from '../validators/enrollment.validator.js';

const router = Router();

// ── Analytics ──
router.get('/dashboard', authMiddleware, getDashboardStats);
router.get('/funnel', authMiddleware, getFunnel);
router.get('/district/:name', authMiddleware, getDistrictStats);
router.get('/skills-heatmap', authMiddleware, getSkillsHeatmap);

// ── Taxonomy (used by Layer 1 for skill mapping) ──
router.get('/taxonomy', authMiddleware, getTaxonomy);

// ── Follow-ups (Dev B integration) ──
router.post('/followups', authMiddleware, validate(createFollowupSchema), createFollowup);
router.get('/followups/pending', authMiddleware, getPendingFollowups);
router.patch('/followups/:id', authMiddleware, updateFollowup);

// ── Outcomes (Dev B integration) ──
router.post('/outcomes', authMiddleware, validate(createOutcomeSchema), createOutcome);
router.get('/outcomes/:beneficiaryId', authMiddleware, getOutcomes);

export default router;
