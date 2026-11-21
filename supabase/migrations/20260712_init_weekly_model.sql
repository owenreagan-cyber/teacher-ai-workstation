-- Phase R2 canonical weekly model (SQLite-targeted migration naming parity).
-- Note: JSONB is used as a logical type label; SQLite stores JSON as TEXT affinity.

CREATE TABLE IF NOT EXISTS weekly_plan (
  id TEXT PRIMARY KEY,
  week_code TEXT NOT NULL,
  school_year TEXT NOT NULL,
  quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
  subject TEXT NOT NULL,
  day TEXT NOT NULL CHECK (day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')),
  date TEXT,
  entry_type TEXT NOT NULL DEFAULT 'lesson',
  lesson_number INTEGER,
  topic TEXT,
  in_class TEXT NOT NULL DEFAULT '',
  at_home TEXT NOT NULL DEFAULT '',
  homework_type TEXT,
  resources JSONB NOT NULL DEFAULT '[]' CHECK (json_valid(resources)),
  reminders JSONB NOT NULL DEFAULT '[]' CHECK (json_valid(reminders)),
  notes TEXT,
  no_class BOOLEAN NOT NULL DEFAULT 0 CHECK (no_class IN (0, 1)),
  save_state TEXT NOT NULL DEFAULT 'draft'
);

-- Prevent duplicate rows for the same logical slot.
CREATE UNIQUE INDEX IF NOT EXISTS idx_weekly_plan_slot
  ON weekly_plan (week_code, school_year, subject, day);

CREATE INDEX IF NOT EXISTS idx_weekly_plan_week
  ON weekly_plan (week_code, day, subject);

-- Local state companion table for selected week and lightweight state metadata.
CREATE TABLE IF NOT EXISTS weekly_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
