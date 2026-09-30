import { Router } from 'express';
import {
  registerBeneficiary, listBeneficiaries, getBeneficiary,
  updateBeneficiary, getBeneficiarySkills, updateBeneficiaryStatus,
  checkPhone, getBeneficiaryRecommendations
} from '../controllers/beneficiary.controller.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware } from '../middleware/auth.js';
import {
  registerBeneficiarySchema, updateBeneficiarySchema, updateStatusSchema
} from '../validators/beneficiary.validator.js';

const router = Router();

// Layer 1 calls this — uses API key auth
router.post('/register',
  authMiddleware,
  validate(registerBeneficiarySchema),
  registerBeneficiary
);

// Dashboard + services
router.get('/', authMiddleware, listBeneficiaries);

// Check if phone exists (Layer 1 deduplication)
router.get('/phone/:phone', authMiddleware, checkPhone);

// Single beneficiary
router.get('/:id', authMiddleware, getBeneficiary);
router.put('/:id', authMiddleware, validate(updateBeneficiarySchema), updateBeneficiary);
router.get('/:id/skills', authMiddleware, getBeneficiarySkills);
router.get('/:id/recommendations', authMiddleware, getBeneficiaryRecommendations);
router.patch('/:id/status', authMiddleware, validate(updateStatusSchema), updateBeneficiaryStatus);

export default router;
