#!/usr/bin/env python3
"""
store.py — 院校数据底座（SQLite）

表：
  universities   院校主表（slug 唯一）
  cds_records    CDS 年度快照（录取/标化/截止/费用）
  sources        来源台账（url + sha256 + 抓取时间）→ 每条数据可溯源

用法：
  store.py init                    建库
  store.py ingest --univ mit --year 2025 --text cds.txt [--meta m.json] [--url U]
  store.py query  --univ mit
  store.py list
  store.py export --out colleges.csv
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from cds_parse import parse as parse_cds  # noqa: E402

DEFAULT_DB = os.path.expanduser("~/.hermes/profiles/joe/data/college.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS universities (
  slug        TEXT PRIMARY KEY,
  name_en     TEXT,
  name_cn     TEXT,
  country     TEXT DEFAULT 'US',
  city        TEXT,
  us_news     INTEGER,
  qs_rank     INTEGER,
  updated_at  TEXT
);
CREATE TABLE IF NOT EXISTS cds_records (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  univ_slug       TEXT NOT NULL REFERENCES universities(slug),
  cds_year        INTEGER NOT NULL,
  applied         REAL, admitted REAL, enrolled REAL, admission_rate REAL,
  sat_ebrw_25     REAL, sat_ebrw_75 REAL,
  sat_math_25     REAL, sat_math_75 REAL,
  act_25          REAL, act_75 REAL,
  ed_deadline     TEXT, ea_deadline TEXT, rd_deadline TEXT,
  tuition         REAL, room_board REAL,
  coverage        TEXT,
  missing_fields  TEXT,
  source_url      TEXT,
  source_sha256   TEXT,
  parsed_at       TEXT,
  UNIQUE(univ_slug, cds_year)
);
CREATE TABLE IF NOT EXISTS sources (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  univ_slug   TEXT,
  cds_year    INTEGER,
  url         TEXT,
  sha256      TEXT,
  fetched_at  TEXT,
  note        TEXT
);
CREATE TABLE IF NOT EXISTS cds_factors (
  univ_slug   TEXT NOT NULL,
  cds_year    INTEGER NOT NULL,
  factor      TEXT NOT NULL,
  importance  TEXT,
  PRIMARY KEY (univ_slug, cds_year, factor)
);
CREATE INDEX IF NOT EXISTS idx_cds_univ ON cds_records(univ_slug);
"""


def connect(db_path, init=False):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if init:
        conn.executescript(SCHEMA)
        conn.commit()
    return conn


def upsert_university(conn, slug, meta):
    conn.execute(
        """INSERT INTO universities (slug, name_en, name_cn, country, city, us_news, qs_rank, updated_at)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(slug) DO UPDATE SET
             name_en=COALESCE(excluded.name_en, name_en),
             name_cn=COALESCE(excluded.name_cn, name_cn),
             us_news=COALESCE(excluded.us_news, us_news),
             qs_rank=COALESCE(excluded.qs_rank, qs_rank),
             updated_at=excluded.updated_at""",
        (slug, meta.get("name_en"), meta.get("name_cn"), meta.get("country", "US"),
         meta.get("city"), meta.get("us_news"), meta.get("qs_rank"),
         datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")))


def cmd_init(a):
    conn = connect(a.db, init=True)
    print(f"✅ 建库完成: {a.db}")
    conn.close()
    return 0


def cmd_ingest(a):
    text = open(a.text, encoding="utf-8", errors="ignore").read()
    meta = json.load(open(a.meta, encoding="utf-8")) if a.meta else {}
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    data = parse_cds(text, meta)
    c1, c9, c11, cost = data["c1_admissions"], data["c9_test_scores"], data["c11_deadlines"], data["costs"]

    conn = connect(a.db, init=True)
    upsert_university(conn, a.univ, meta)
    conn.execute(
        """INSERT INTO cds_records (univ_slug, cds_year, applied, admitted, enrolled, admission_rate,
             sat_ebrw_25, sat_ebrw_75, sat_math_25, sat_math_75, act_25, act_75,
             ed_deadline, ea_deadline, rd_deadline, tuition, room_board,
             coverage, missing_fields, source_url, source_sha256, parsed_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(univ_slug, cds_year) DO UPDATE SET
             applied=excluded.applied, admitted=excluded.admitted, enrolled=excluded.enrolled,
             admission_rate=excluded.admission_rate,
             sat_ebrw_25=excluded.sat_ebrw_25, sat_ebrw_75=excluded.sat_ebrw_75,
             sat_math_25=excluded.sat_math_25, sat_math_75=excluded.sat_math_75,
             act_25=excluded.act_25, act_75=excluded.act_75,
             ed_deadline=excluded.ed_deadline, ea_deadline=excluded.ea_deadline, rd_deadline=excluded.rd_deadline,
             tuition=excluded.tuition, room_board=excluded.room_board,
             coverage=excluded.coverage, missing_fields=excluded.missing_fields,
             source_url=excluded.source_url, source_sha256=excluded.source_sha256,
             parsed_at=excluded.parsed_at""",
        (a.univ, a.year, c1["applied"], c1["admitted"], c1["enrolled"], c1["admission_rate"],
         c9["sat_ebrw_25"], c9["sat_ebrw_75"], c9["sat_math_25"], c9["sat_math_75"], c9["act_25"], c9["act_75"],
         c11["deadlines"].get("ED"), c11["deadlines"].get("EA"), c11["deadlines"].get("RD"),
         cost["tuition"], cost["room_board"],
         data["coverage"], json.dumps(data["missing"], ensure_ascii=False),
         a.url, sha, datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")))
    factors = (data.get("c7_factors") or {}).get("factors") or {}
    conn.execute("DELETE FROM cds_factors WHERE univ_slug=? AND cds_year=?", (a.univ, a.year))
    for fk, imp in factors.items():
        conn.execute("INSERT OR REPLACE INTO cds_factors (univ_slug, cds_year, factor, importance) VALUES (?,?,?,?)",
                     (a.univ, a.year, fk, imp))
    conn.execute("INSERT INTO sources (univ_slug, cds_year, url, sha256, fetched_at, note) VALUES (?,?,?,?,?,?)",
                 (a.univ, a.year, a.url, sha,
                  datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "cds_parse"))
    conn.commit()
    print(json.dumps({"univ": a.univ, "year": a.year, "coverage": data["coverage"],
                      "missing": data["missing"], "c7_factors": len(factors), "sha256": sha[:16]}, ensure_ascii=False))
    conn.close()
    return 0


def cmd_query(a):
    conn = connect(a.db)
    rows = conn.execute(
        """SELECT u.slug, u.name_en, u.name_cn, r.cds_year, r.admission_rate,
                  r.sat_ebrw_25, r.sat_ebrw_75, r.sat_math_25, r.sat_math_75, r.act_25, r.act_75,
                  r.ed_deadline, r.ea_deadline, r.rd_deadline, r.tuition, r.room_board, r.coverage
           FROM cds_records r JOIN universities u ON u.slug = r.univ_slug
           WHERE (? IS NULL OR u.slug = ?) ORDER BY r.cds_year DESC""", (a.univ, a.univ)).fetchall()
    if not rows:
        print("无记录")
        return 1
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    return 0


def cmd_list(a):
    conn = connect(a.db)
    for r in conn.execute("SELECT slug, name_cn, country FROM universities ORDER BY slug"):
        print(f'{r["slug"]:12s} {r["name_cn"] or ""} ({r["country"]})')
    return 0


def cmd_export(a):
    conn = connect(a.db)
    rows = conn.execute(
        """SELECT u.slug, u.name_cn, r.cds_year, r.admission_rate, r.sat_ebrw_25, r.sat_ebrw_75,
                  r.sat_math_25, r.sat_math_75, r.act_25, r.act_75, r.tuition, r.room_board, r.coverage
           FROM cds_records r JOIN universities u ON u.slug=r.univ_slug ORDER BY u.slug, r.cds_year""").fetchall()
    if not rows:
        print("无数据")
        return 1
    cols = rows[0].keys()
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join("" if r[c] is None else str(r[c]) for c in cols) + "\n")
    print(f"导出 {len(rows)} 行 → {a.out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="院校数据底座")
    ap.add_argument("--db", default=DEFAULT_DB)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest")
    p.add_argument("--univ", required=True, help="院校 slug，如 mit")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--text", required=True, help="CDS 纯文本文件")
    p.add_argument("--meta", help="院校元数据 JSON")
    p.add_argument("--url", help="来源 URL")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("query"); p.add_argument("--univ"); p.set_defaults(func=cmd_query)
    p = sub.add_parser("list"); p.set_defaults(func=cmd_list)
    p = sub.add_parser("export"); p.add_argument("--out", required=True); p.set_defaults(func=cmd_export)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
