"""
Database Exporter — Schemes & Courses Database to SQLite
=========================================================
Exports Government Schemes, NSQF Courses, Skills, and Training Centers
into the production SQLite relational database:
  data/vanisetu.db

Run with:
  python services/recommendation_engine/data/export_to_sqlite.py
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "vanisetu.db"


def export_to_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure NO person or beneficiary data exists in the database
    cursor.execute("DROP TABLE IF EXISTS beneficiaries")
    cursor.execute("DROP TABLE IF EXISTS persons")
    cursor.execute("DROP TABLE IF EXISTS beneficiary_records")

    # 1. PM-AJAY Yojana & Converged Government Schemes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        scheme_id TEXT PRIMARY KEY,
        scheme_name TEXT NOT NULL,
        ministry TEXT,
        sectors TEXT,
        target_audience TEXT,
        min_education TEXT,
        min_age INTEGER,
        max_age INTEGER,
        caste_criteria TEXT,
        employment_type TEXT,
        financial_grant TEXT,
        stipend_amount TEXT,
        loan_subsidy TEXT,
        toolkit_support TEXT,
        training_provided BOOLEAN,
        key_benefits TEXT,
        official_portal TEXT
    )
    """)

    schemes_file = DATA_DIR / "schemes.json"
    if schemes_file.exists():
        with open(schemes_file, "r", encoding="utf-8") as f:
            schemes = json.load(f)
        cursor.execute("DELETE FROM schemes")
        for s in schemes:
            cursor.execute(
                """INSERT INTO schemes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    s["scheme_id"],
                    s["scheme_name"],
                    s.get("ministry", ""),
                    json.dumps(s.get("sectors", ["All"]), ensure_ascii=False),
                    s.get("target_audience", ""),
                    s.get("min_education", "none"),
                    s.get("min_age", 18),
                    s.get("max_age", 65),
                    s.get("caste_criteria", "all"),
                    s.get("employment_type", "both"),
                    s.get("financial_grant", ""),
                    s.get("stipend_amount", ""),
                    s.get("loan_subsidy", ""),
                    s.get("toolkit_support", ""),
                    1 if s.get("training_provided", True) else 0,
                    s.get("key_benefits", ""),
                    s.get("official_portal", ""),
                ),
            )
        print(f"[OK] Exported {len(schemes)} Government Schemes into table 'schemes'")

    # 2. Courses (Qualifications) Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        sector TEXT NOT NULL,
        occupation TEXT,
        description TEXT,
        nsqf_level INTEGER,
        min_education TEXT,
        min_experience_years REAL,
        supports_rpl BOOLEAN,
        required_skills TEXT,
        optional_skills TEXT,
        is_active BOOLEAN
    )
    """)

    # Also keep qualifications table for backwards compatibility
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qualifications (
        qualification_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        sector TEXT NOT NULL,
        occupation TEXT,
        description TEXT,
        nsqf_level INTEGER,
        min_education TEXT,
        min_experience_years REAL,
        supports_rpl BOOLEAN,
        required_skills TEXT,
        optional_skills TEXT,
        is_active BOOLEAN
    )
    """)

    quals_file = DATA_DIR / "qualifications.json"
    if quals_file.exists():
        with open(quals_file, "r", encoding="utf-8") as f:
            quals = json.load(f)
        cursor.execute("DELETE FROM courses")
        cursor.execute("DELETE FROM qualifications")
        for q in quals:
            row = (
                q["qualification_id"],
                q["title"],
                q["sector"],
                q.get("occupation", ""),
                q.get("description", ""),
                q.get("nsqf_level", 1),
                q.get("min_education", "none"),
                q.get("min_experience_years", 0),
                1 if q.get("supports_rpl") else 0,
                json.dumps(q.get("required_skills", [])),
                json.dumps(q.get("optional_skills", [])),
                1 if q.get("is_active", True) else 0,
            )
            cursor.execute("""INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
            cursor.execute("""INSERT INTO qualifications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
        print(f"[OK] Exported {len(quals)} NSQF Courses into tables 'courses' & 'qualifications'")

    # 3. Skills Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        skill_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sector TEXT NOT NULL,
        aliases TEXT
    )
    """)

    skills_file = DATA_DIR / "skills.json"
    if skills_file.exists():
        with open(skills_file, "r", encoding="utf-8") as f:
            skills = json.load(f)
        cursor.execute("DELETE FROM skills")
        for s in skills:
            cursor.execute(
                "INSERT INTO skills VALUES (?, ?, ?, ?)",
                (s["skill_id"], s["name"], s["sector"], json.dumps(s.get("aliases", []), ensure_ascii=False)),
            )
        print(f"[OK] Exported {len(skills)} skills into table 'skills'")

    # 4. Training Centers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_centers (
        center_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        district TEXT,
        state TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        authorized BOOLEAN,
        supported_qualifications TEXT
    )
    """)

    centers_file = DATA_DIR / "centers.json"
    if centers_file.exists():
        with open(centers_file, "r", encoding="utf-8") as f:
            centers = json.load(f)
        cursor.execute("DELETE FROM training_centers")
        for c in centers:
            cursor.execute(
                """INSERT INTO training_centers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    c["center_id"],
                    c["name"],
                    c.get("district", ""),
                    c.get("state", ""),
                    c.get("address", ""),
                    c.get("latitude", 0.0),
                    c.get("longitude", 0.0),
                    1 if c.get("authorized", True) else 0,
                    json.dumps(c.get("supported_qualifications", [])),
                ),
            )
        print(f"[OK] Exported {len(centers)} centers into table 'training_centers'")

    # 5. Batches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        batch_id TEXT PRIMARY KEY,
        qualification_id TEXT,
        center_id TEXT,
        start_date TEXT,
        end_date TEXT,
        capacity INTEGER,
        seats_available INTEGER,
        status TEXT
    )
    """)

    batches_file = DATA_DIR / "batches.json"
    if batches_file.exists():
        with open(batches_file, "r", encoding="utf-8") as f:
            batches = json.load(f)
        cursor.execute("DELETE FROM batches")
        for b in batches:
            cursor.execute(
                """INSERT INTO batches VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    b["batch_id"],
                    b["qualification_id"],
                    b["center_id"],
                    b.get("start_date", ""),
                    b.get("end_date", ""),
                    b.get("capacity", 30),
                    b.get("seats_available", 30),
                    b.get("status", "upcoming"),
                ),
            )
        print(f"[OK] Exported {len(batches)} batches into table 'batches'")

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Relational database updated at: {DB_PATH}")


if __name__ == "__main__":
    export_to_sqlite()
