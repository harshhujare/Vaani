import { Router } from 'express';
import { registerUser, loginUser, getMe } from '../controllers/auth.controller.js';
import { verifyToken } from '../middleware/auth.js';
import { z } from 'zod';
import { validate } from '../middleware/validate.js';

const router = Router();

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'district_officer', 'state_officer', 'training_center', 'viewer']).optional(),
  district: z.string().max(100).optional(),
  state: z.string().max(100).optional(),
});

// Public routes
router.post('/login', validate(loginSchema), loginUser);
router.post('/register', validate(registerSchema), registerUser);

// Protected route
router.get('/me', verifyToken, getMe);

export default router;
