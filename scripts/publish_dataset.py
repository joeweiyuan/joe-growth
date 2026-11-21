#!/usr/bin/env python3
"""把 college.db 发布为「云策可读的固定数据集」→ /root/shared/offerpath/

产出：
  college.db          SQLite 权威库（只读副本）
  schema.sql          建表语句
  exports/*.csv       四张表全量导出（UTF-8 BOM，Excel 可直接开）
  exports/*.json      程序接入用（含质量标记）
  manifest.json       版本/行数/校验和/生成时间
"""
import csv
import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime

SRC_DB = "/root/.hermes/profiles/joe/data/college.db"
OUT = "/root/shared/offerpath"
EXPORTS = os.path.join(OUT, "exports")
TABLES = ["universities", "cds_records", "cds_factors", "cds_sources"]


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(EXPORTS, exist_ok=True)
    if not os.path.exists(SRC_DB):
        raise SystemExit(f"源库不存在: {SRC_DB}")

    # 1) 复制权威库（VACUUM 成单文件，避免 WAL 依赖）
    dst_db = os.path.join(OUT, "college.db")
    tmp = os.path.join(OUT, "_tmp.db")
    shutil.copy2(SRC_DB, tmp)
    conn = sqlite3.connect(tmp)
    conn.execute("VACUUM")
    conn.close()
    os.replace(tmp, dst_db)

    # 2) schema.sql
    conn = sqlite3.connect(dst_db)
    schema = "\n".join(r[0] for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL"))
    open(os.path.join(OUT, "schema.sql"), "w", encoding="utf-8").write(schema + "\n")

    # 3) 导出
    counts = {}
    for t in TABLES:
        try:
            cur = conn.execute(f"SELECT * FROM {t}")
        except sqlite3.Error:
            counts[t] = 0
            continue
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        counts[t] = len(rows)

        with open(os.path.join(EXPORTS, f"{t}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)

        with open(os.path.join(EXPORTS, f"{t}.json"), "w", encoding="utf-8") as f:
            json.dump([dict(zip(cols, r)) for r in rows], f, ensure_ascii=False, indent=2)

    # 4) 质量汇总（给产品用：哪些校可用于评分）
    q = conn.execute("""SELECT u.slug, u.name_cn, r.cds_year, r.admission_rate, r.quality, r.quality_note
                        FROM cds_records r JOIN universities u ON u.slug=r.univ_slug
                        ORDER BY r.quality, u.slug""").fetchall()
    conn.close()

    manifest = {
        "dataset": "offerpath-college-dataset",
        "version": datetime.now().strftime("%Y%m%d.%H%M"),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "owner": "六六 (joe profile)",
        "consumer": "云策 (dad profile) / OfferPath MVP",
        "source_of_truth": dst_db,
        "tables": counts,
        "schools": [{"slug": r[0], "name_cn": r[1], "cds_year": r[2],
                     "admission_rate": r[3], "quality": r[4], "quality_note": r[5]} for r in q],
        "quality_semantics": {
            "ok": "该区块解析可信，可用于评分",
            "suspicious": "结构完整但取值异常，需人工复核后才可用",
            "partial": "部分区块缺失",
            "unparsed": "未解析出，不得当作 0 使用",
        },
        "checksums": {f: sha256(os.path.join(OUT, f)) for f in ("college.db", "schema.sql")},
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(json.dumps({"out": OUT, "tables": counts,
                      "db_sha256": manifest["checksums"]["college.db"][:16]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
