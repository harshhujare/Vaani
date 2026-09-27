/**
 * Reusable pagination helper for list endpoints
 * Usage: const { offset, limit, page } = getPagination(req.query);
 */

export const getPagination = (query) => {
  const page = Math.max(1, parseInt(query.page) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(query.limit) || 20));
  const offset = (page - 1) * limit;
  return { page, limit, offset };
};

export const getPaginationMeta = (page, limit, total) => ({
  page,
  limit,
  total,
  totalPages: Math.ceil(total / limit),
});
