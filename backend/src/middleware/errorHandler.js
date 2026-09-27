import { sendError } from '../utils/apiResponse.js';

/**
 * Global error handler middleware
 * Catches all unhandled errors and returns consistent format
 */
export const errorHandler = (err, req, res, next) => {
  console.error('❌ Error:', err.message);

  if (err.name === 'ZodError') {
    const errors = err.errors.map((e) => ({
      field: e.path.join('.'),
      message: e.message,
    }));
    return sendError(res, 'Validation failed', 400, errors);
  }

  if (err.code === '23505') {
    // PostgreSQL unique constraint violation
    return sendError(res, 'Duplicate entry. Resource already exists.', 409);
  }

  if (err.code === '23503') {
    // PostgreSQL foreign key violation
    return sendError(res, 'Referenced resource not found.', 400);
  }

  const statusCode = err.statusCode || 500;
  const message = err.statusCode ? err.message : 'Internal server error';

  return sendError(res, message, statusCode);
};

/**
 * Custom error class with status code
 */
export class ApiError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
  }
}
