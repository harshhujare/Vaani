import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { config } from './config/env.js';
import { errorHandler } from './middleware/errorHandler.js';

// Route imports
import authRoutes from './routes/auth.routes.js';
import beneficiaryRoutes from './routes/beneficiary.routes.js';
import programRoutes from './routes/program.routes.js';
import callLogRoutes from './routes/callLog.routes.js';
import enrollmentRoutes from './routes/enrollment.routes.js';
import attendanceRoutes from './routes/attendance.routes.js';
import analyticsRoutes from './routes/analytics.routes.js';

const app = express();

// ── Middleware ──
app.use(cors({
  origin: config.FRONTEND_URL,
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));

// ── Health Check ──
app.get('/health', (req, res) => {
  res.json({
    success: true,
    message: 'VaniSetu Platform API is running',
    timestamp: new Date().toISOString(),
    environment: config.NODE_ENV,
  });
});

// ── API Routes ──
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/beneficiary', beneficiaryRoutes);
app.use('/api/v1/beneficiaries', beneficiaryRoutes);  // alias for list
app.use('/api/v1/programs', programRoutes);
app.use('/api/v1/call-logs', callLogRoutes);
app.use('/api/v1/enrollments', enrollmentRoutes);
app.use('/api/v1/attendance', attendanceRoutes);
app.use('/api/v1/analytics', analyticsRoutes);

// ── 404 Handler ──
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: `Route ${req.method} ${req.originalUrl} not found`,
  });
});

// ── Global Error Handler ──
app.use(errorHandler);

// ── Start Server ──
app.listen(config.PORT, () => {
  console.log(`
  ╔═══════════════════════════════════════════════╗
  ║  🚀 VaniSetu Platform API                    ║
  ║  Running on: http://localhost:${config.PORT}        ║
  ║  Environment: ${config.NODE_ENV.padEnd(30)}║
  ╚═══════════════════════════════════════════════╝
  `);
});

export default app;
