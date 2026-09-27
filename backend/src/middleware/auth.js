import jwt from 'jsonwebtoken';
import { config } from '../config/env.js';
import { sendError } from '../utils/apiResponse.js';

/**
 * Verify JWT token from Authorization header
 */
export const verifyToken = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return sendError(res, 'Access denied. No token provided.', 401);
  }

  try {
    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, config.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return sendError(res, 'Invalid or expired token.', 401);
  }
};

/**
 * Check API key for service-to-service communication (Layer 1, Dev B)
 */
export const verifyApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    return sendError(res, 'Access denied. No API key provided.', 401);
  }

  if (apiKey === config.LAYER1_API_KEY || apiKey === config.DEVB_API_KEY) {
    req.serviceAuth = true;
    next();
  } else {
    return sendError(res, 'Invalid API key.', 401);
  }
};

/**
 * Combined auth: accepts either JWT token OR API key
 * Use this for endpoints that both the dashboard and services call
 */
export const authMiddleware = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  const authHeader = req.headers.authorization;

  // Try API key first (service-to-service)
  if (apiKey) {
    if (apiKey === config.LAYER1_API_KEY || apiKey === config.DEVB_API_KEY) {
      req.serviceAuth = true;
      return next();
    }
    return sendError(res, 'Invalid API key.', 401);
  }

  // Then try JWT (dashboard users)
  if (authHeader && authHeader.startsWith('Bearer ')) {
    try {
      const token = authHeader.split(' ')[1];
      const decoded = jwt.verify(token, config.JWT_SECRET);
      req.user = decoded;
      return next();
    } catch (error) {
      return sendError(res, 'Invalid or expired token.', 401);
    }
  }

  return sendError(res, 'Access denied. Provide API key or JWT token.', 401);
};

/**
 * Role-based access control
 * Usage: router.get('/route', verifyToken, requireRole('admin', 'district_officer'), controller)
 */
export const requireRole = (...roles) => {
  return (req, res, next) => {
    // Service auth bypasses role check
    if (req.serviceAuth) return next();

    if (!req.user || !roles.includes(req.user.role)) {
      return sendError(res, `Access denied. Required roles: ${roles.join(', ')}`, 403);
    }
    next();
  };
};
