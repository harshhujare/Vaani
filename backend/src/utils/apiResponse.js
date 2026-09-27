/**
 * Standardized API response helper
 * All endpoints use this for consistent response format
 */

export const sendSuccess = (res, data, message = 'Success', statusCode = 200, meta = null) => {
  const response = {
    success: true,
    data,
    message,
  };
  if (meta) response.meta = meta;
  return res.status(statusCode).json(response);
};

export const sendCreated = (res, data, message = 'Created successfully') => {
  return sendSuccess(res, data, message, 201);
};

export const sendError = (res, message = 'Internal server error', statusCode = 500, errors = null) => {
  const response = {
    success: false,
    data: null,
    message,
  };
  if (errors) response.errors = errors;
  return res.status(statusCode).json(response);
};
