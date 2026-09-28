import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import { config } from './env.js';
import * as schema from '../db/schema.js';

if (!config.DATABASE_URL) {
  console.error('❌ DATABASE_URL is not set in .env');
  process.exit(1);
}

const sql = neon(config.DATABASE_URL);
export const db = drizzle(sql, { schema });

export { sql };

