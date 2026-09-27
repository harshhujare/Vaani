import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { db } from '../config/db.js';
import { users } from '../db/schema.js';
import { eq } from 'drizzle-orm';
import { config } from '../config/env.js';
import { sendSuccess, sendCreated, sendError } from '../utils/apiResponse.js';

/**
 * POST /api/v1/auth/register
 * Create a new user (admin creates other users)
 */
export const registerUser = async (req, res, next) => {
  try {
    const { email, password, name, role, district, state } = req.body;

    // Check if user exists
    const existing = await db.select({ id: users.id })
      .from(users)
      .where(eq(users.email, email))
      .limit(1);

    if (existing.length > 0) {
      return sendError(res, 'User with this email already exists', 409);
    }

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    // Create user
    const [user] = await db.insert(users).values({
      email,
      passwordHash,
      name,
      role: role || 'viewer',
      district,
      state,
    }).returning({
      id: users.id,
      email: users.email,
      name: users.name,
      role: users.role,
    });

    return sendCreated(res, user, 'User created successfully');

  } catch (error) {
    next(error);
  }
};

/**
 * POST /api/v1/auth/login
 * Login and get JWT token
 */
export const loginUser = async (req, res, next) => {
  try {
    const { email, password } = req.body;

    // Find user
    const [user] = await db.select()
      .from(users)
      .where(eq(users.email, email))
      .limit(1);

    if (!user) {
      return sendError(res, 'Invalid email or password', 401);
    }

    if (!user.isActive) {
      return sendError(res, 'Account is deactivated. Contact admin.', 403);
    }

    // Verify password
    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
      return sendError(res, 'Invalid email or password', 401);
    }

    // Generate JWT
    const token = jwt.sign(
      {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
        district: user.district,
        state: user.state,
      },
      config.JWT_SECRET,
      { expiresIn: config.JWT_EXPIRES_IN }
    );

    return sendSuccess(res, {
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
        district: user.district,
      }
    }, 'Login successful');

  } catch (error) {
    next(error);
  }
};

/**
 * GET /api/v1/auth/me
 * Get current user profile from JWT
 */
export const getMe = async (req, res, next) => {
  try {
    const [user] = await db.select({
      id: users.id,
      email: users.email,
      name: users.name,
      role: users.role,
      district: users.district,
      state: users.state,
    })
      .from(users)
      .where(eq(users.id, req.user.id))
      .limit(1);

    if (!user) {
      return sendError(res, 'User not found', 404);
    }

    return sendSuccess(res, user, 'User profile fetched');

  } catch (error) {
    next(error);
  }
};
