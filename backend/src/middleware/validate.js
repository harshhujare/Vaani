/**
 * Zod validation middleware factory
 * Usage: router.post('/route', validate(myZodSchema), controller)
 */
export const validate = (schema) => {
  return (req, res, next) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      next(error); // errorHandler catches ZodError
    }
  };
};

/**
 * Validate query parameters
 */
export const validateQuery = (schema) => {
  return (req, res, next) => {
    try {
      req.query = schema.parse(req.query);
      next();
    } catch (error) {
      next(error);
    }
  };
};
