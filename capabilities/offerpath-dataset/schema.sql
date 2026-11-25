CREATE TABLE universities (
  slug TEXT PRIMARY KEY, name_en TEXT, name_cn TEXT, country TEXT DEFAULT 'US',
  city TEXT, us_news INTEGER, qs_rank INTEGER, updated_at TEXT)
CREATE TABLE cds_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  univ_slug TEXT NOT NULL, cds_year INTEGER NOT NULL,
  applied REAL, admitted REAL, enrolled REAL, admission_rate REAL,
  sat_ebrw_25 REAL, sat_ebrw_75 REAL, sat_math_25 REAL, sat_math_75 REAL,
  act_25 REAL, act_75 REAL,
  ed_deadline TEXT, ea_deadline TEXT, rd_deadline TEXT,
  tuition REAL, room_board REAL,
  coverage TEXT, missing_fields TEXT,
  source_url TEXT, source_sha256 TEXT, parsed_at TEXT,
  quality TEXT, quality_note TEXT,
  UNIQUE(univ_slug, cds_year))
CREATE TABLE sqlite_sequence(name,seq)
CREATE TABLE cds_factors (
  univ_slug TEXT NOT NULL, cds_year INTEGER NOT NULL, factor TEXT NOT NULL,
  importance TEXT, quality TEXT, PRIMARY KEY (univ_slug, cds_year, factor))
CREATE TABLE cds_sources (
  slug TEXT PRIMARY KEY, url TEXT, last_status TEXT, last_error TEXT, updated_at TEXT)
