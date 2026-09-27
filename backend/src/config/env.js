import dotenv from 'dotenv';
dotenv.config();

export const config = {
  PORT: process.env.PORT || 3001,
  NODE_ENV: process.env.NODE_ENV || 'development',
  DATABASE_URL: process.env.DATABASE_URL,
  JWT_SECRET: process.env.JWT_SECRET || 'dev-secret-change-me',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',
  LAYER1_API_KEY: process.env.LAYER1_API_KEY,
  DEVB_API_KEY: process.env.DEVB_API_KEY,
  FRONTEND_URL: process.env.FRONTEND_URL || 'http://localhost:5173',
};
