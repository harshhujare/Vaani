/**
 * Seed script — populates the database with sample data
 * Run: npm run db:seed
 */

import dotenv from 'dotenv';
dotenv.config();

import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';
import { nsqfTaxonomy, trainingPrograms, beneficiaries, beneficiarySkills, users } from './schema.js';
import bcrypt from 'bcryptjs';

const sql = neon(process.env.DATABASE_URL);
const db = drizzle(sql);

async function seed() {
  console.log('🌱 Starting seed...\n');

  // ── 1. Seed NSQF Taxonomy ──
  console.log('📚 Seeding NSQF Taxonomy...');
  await db.insert(nsqfTaxonomy).values([
    {
      sector: 'Construction',
      subSector: 'Carpentry',
      skillName: 'Furniture Maker',
      nsqfLevel: 4,
      qualificationPack: 'CON/Q0302',
      description: 'Makes wooden furniture like chairs, tables, beds, almirahs',
      keywords: ['furniture', 'lakdi', 'carpenter', 'wood', 'almari', 'kursi', 'table'],
    },
    {
      sector: 'Construction',
      subSector: 'Masonry',
      skillName: 'Mason (General)',
      nsqfLevel: 4,
      qualificationPack: 'CON/Q0103',
      description: 'Brick laying, plastering, basic construction',
      keywords: ['mason', 'mistri', 'rajgir', 'eent', 'plaster', 'cement', 'construction'],
    },
    {
      sector: 'Construction',
      subSector: 'Plumbing',
      skillName: 'Plumber (General)',
      nsqfLevel: 3,
      qualificationPack: 'CON/Q0601',
      description: 'Pipe fitting, water supply, drainage',
      keywords: ['plumber', 'nalkiwala', 'pipe', 'paani', 'drainage', 'tap'],
    },
    {
      sector: 'Agriculture',
      subSector: 'Organic Farming',
      skillName: 'Organic Farmer',
      nsqfLevel: 4,
      qualificationPack: 'AGR/Q0801',
      description: 'Organic farming techniques, composting, natural pest control',
      keywords: ['organic', 'kheti', 'jaivik', 'compost', 'farming', 'kisan'],
    },
    {
      sector: 'Agriculture',
      subSector: 'Dairy',
      skillName: 'Dairy Farmer',
      nsqfLevel: 3,
      qualificationPack: 'AGR/Q0501',
      description: 'Cattle rearing, milk production, dairy management',
      keywords: ['dairy', 'doodh', 'gaay', 'buffalo', 'milk', 'pashu'],
    },
    {
      sector: 'Textiles',
      subSector: 'Weaving',
      skillName: 'Handloom Weaver',
      nsqfLevel: 4,
      qualificationPack: 'TSC/Q0201',
      description: 'Traditional handloom weaving, pattern design',
      keywords: ['weaving', 'bunai', 'hathkargha', 'kapda', 'saree', 'cloth'],
    },
    {
      sector: 'Textiles',
      subSector: 'Tailoring',
      skillName: 'Tailor (Self-employed)',
      nsqfLevel: 3,
      qualificationPack: 'TSC/Q0302',
      description: 'Stitching, alteration, garment making',
      keywords: ['tailor', 'darzi', 'silai', 'stitching', 'kapda', 'machine'],
    },
    {
      sector: 'Electronics',
      subSector: 'Mobile Repair',
      skillName: 'Mobile Phone Technician',
      nsqfLevel: 4,
      qualificationPack: 'ELE/Q8104',
      description: 'Mobile phone repair, hardware and software troubleshooting',
      keywords: ['mobile', 'phone', 'repair', 'samsung', 'screen', 'battery'],
    },
    {
      sector: 'Beauty & Wellness',
      subSector: 'Hair & Skin',
      skillName: 'Beauty Therapist',
      nsqfLevel: 3,
      qualificationPack: 'BWS/Q0101',
      description: 'Hair cutting, skin care, basic beauty services',
      keywords: ['beauty', 'parlour', 'hair', 'baal', 'facial', 'makeup'],
    },
    {
      sector: 'Automotive',
      subSector: 'Two-Wheeler',
      skillName: 'Two-Wheeler Mechanic',
      nsqfLevel: 3,
      qualificationPack: 'ASC/Q1411',
      description: 'Repair and servicing of motorcycles and scooters',
      keywords: ['mechanic', 'bike', 'scooter', 'motorcycle', 'gaadi', 'engine'],
    },
  ]).onConflictDoNothing();
  console.log('  ✅ 10 taxonomy entries seeded');

  // ── 2. Seed Training Programs ──
  console.log('📋 Seeding Training Programs...');
  await db.insert(trainingPrograms).values([
    {
      name: 'Advanced Carpentry & Furniture Design',
      sector: 'Construction',
      subSector: 'Carpentry',
      nsqfLevel: 5,
      durationDays: 90,
      district: 'Ranchi',
      state: 'Jharkhand',
      trainingCenter: 'PM-AJAY Skill Center, Ranchi',
      provider: 'National Skill Development Corporation',
      capacity: 30,
      startDate: '2025-11-01',
      endDate: '2026-01-30',
      certification: 'NSQF Level 5 Certificate - Carpentry',
    },
    {
      name: 'Organic Farming Techniques',
      sector: 'Agriculture',
      subSector: 'Organic Farming',
      nsqfLevel: 4,
      durationDays: 45,
      district: 'Ranchi',
      state: 'Jharkhand',
      trainingCenter: 'Krishi Vigyan Kendra, Ranchi',
      provider: 'Ministry of Agriculture',
      capacity: 40,
      startDate: '2025-10-15',
      endDate: '2025-11-30',
      certification: 'NSQF Level 4 Certificate - Organic Farming',
    },
    {
      name: 'Mobile Phone Repair Technician',
      sector: 'Electronics',
      subSector: 'Mobile Repair',
      nsqfLevel: 4,
      durationDays: 60,
      district: 'Patna',
      state: 'Bihar',
      trainingCenter: 'ITI Patna',
      provider: 'Samsung Electronics India',
      capacity: 25,
      startDate: '2025-12-01',
      endDate: '2026-01-31',
      certification: 'NSQF Level 4 - Mobile Repair Technician',
    },
    {
      name: 'Handloom Weaving - Advanced Patterns',
      sector: 'Textiles',
      subSector: 'Weaving',
      nsqfLevel: 5,
      durationDays: 120,
      district: 'Varanasi',
      state: 'Uttar Pradesh',
      trainingCenter: 'Weavers Service Centre, Varanasi',
      provider: 'Ministry of Textiles',
      capacity: 20,
      startDate: '2025-10-01',
      endDate: '2026-01-28',
      certification: 'NSQF Level 5 - Handloom Weaving',
    },
    {
      name: 'Beauty Therapist Training',
      sector: 'Beauty & Wellness',
      subSector: 'Hair & Skin',
      nsqfLevel: 4,
      durationDays: 60,
      district: 'Lucknow',
      state: 'Uttar Pradesh',
      trainingCenter: 'VLCC Training Institute',
      provider: 'VLCC Healthcare',
      capacity: 35,
      startDate: '2025-11-15',
      endDate: '2026-01-15',
      certification: 'NSQF Level 4 - Beauty Therapist',
    },
  ]).onConflictDoNothing();
  console.log('  ✅ 5 training programs seeded');

  // ── 3. Seed Sample Beneficiaries ──
  console.log('👥 Seeding Sample Beneficiaries...');
  const [ramesh] = await db.insert(beneficiaries).values([
    {
      phone: '+91-9876543210',
      name: 'Ramesh Kumar',
      age: 35,
      gender: 'male',
      district: 'Ranchi',
      state: 'Jharkhand',
      village: 'Bara Ghaghra',
      casteCategory: 'SC',
      educationLevel: '8th_pass',
      monthlyIncome: 6000,
      householdSize: 5,
      language: 'hi',
      status: 'assessed',
    },
    {
      phone: '+91-9876543211',
      name: 'Sunita Devi',
      age: 28,
      gender: 'female',
      district: 'Ranchi',
      state: 'Jharkhand',
      village: 'Kanke',
      casteCategory: 'SC',
      educationLevel: '10th_pass',
      monthlyIncome: 4000,
      householdSize: 4,
      language: 'hi',
      status: 'registered',
    },
    {
      phone: '+91-9876543212',
      name: 'Mohan Paswan',
      age: 42,
      gender: 'male',
      district: 'Patna',
      state: 'Bihar',
      village: 'Danapur',
      casteCategory: 'SC',
      educationLevel: '5th_pass',
      monthlyIncome: 5500,
      householdSize: 6,
      language: 'hi',
      status: 'registered',
    },
  ]).returning();
  console.log('  ✅ 3 beneficiaries seeded');

  // ── 4. Seed Skills for Ramesh ──
  console.log('🔧 Seeding Skills...');
  await db.insert(beneficiarySkills).values([
    {
      beneficiaryId: ramesh.id,
      skillName: 'Carpentry - Furniture Making',
      sector: 'Construction',
      subSector: 'Woodwork',
      experienceYears: 15,
      isPrimary: true,
      nsqfLevel: 4,
      confidenceScore: 0.92,
      subSkills: ['joinery', 'finishing', 'wood_selection', 'measurement'],
    },
    {
      beneficiaryId: ramesh.id,
      skillName: 'Basic Plumbing',
      sector: 'Construction',
      subSector: 'Plumbing',
      experienceYears: 3,
      isPrimary: false,
      nsqfLevel: 2,
      confidenceScore: 0.71,
      subSkills: ['pipe_fitting'],
    },
  ]);
  console.log('  ✅ 2 skills seeded for Ramesh');

  // ── 5. Seed Admin User ──
  console.log('🔑 Seeding Admin User...');
  const passwordHash = await bcrypt.hash('admin123', 10);
  await db.insert(users).values({
    email: 'admin@vanisetu.in',
    passwordHash,
    name: 'Admin',
    role: 'admin',
    district: 'All',
    state: 'All',
  }).onConflictDoNothing();
  console.log('  ✅ Admin user seeded (admin@vanisetu.in / admin123)');

  console.log('\n🎉 Seed completed successfully!');
  process.exit(0);
}

seed().catch((error) => {
  console.error('❌ Seed failed:', error);
  process.exit(1);
});
