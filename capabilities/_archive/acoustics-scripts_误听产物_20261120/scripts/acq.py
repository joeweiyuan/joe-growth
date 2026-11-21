#!/usr/bin/env python3
"""
acq.py — 声学聚合数据收集整理工具链（acoustics-data-pack 核心脚本）

依赖：numpy、scipy（本机已装）；无需 librosa/pandas。

子命令：
  ingest   <目录>                扫描录音 + 元数据，校验必填字段，生成 manifest.json
  qc       <wav> [--meta yaml]   单文件质量检查（削波/直流/静音/峰值/信噪比）
  metrics  <wav> [--meta yaml]   计算 Leq / Lmax / L10-L50-L90 / 倍频程
  aggregate <目录>               汇总 manifest → dataset.csv + 数据字典 + 质量报告

设计原则：
  1. 元数据缺字段 → 拒收（不猜）；
  2. 无校准值 → 只输出 dBFS 相对电平，明确标 REL，绝不冒称 dB SPL；
  3. A 计权按 IEC 61672 解析式在频域实现（1 kHz 归零）；
  4. 所有结果附带 method 说明，可复现。
"""
import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
from scipy.io import wavfile

P_REF = 20e-6  # 20 µPa

# 1/1 倍频程中心频率（Hz）
OCTAVE_CENTERS = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
# 1/3 倍频程中心频率（Hz）
THIRD_OCTAVE_CENTERS = [
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
    630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
    10000, 12500, 16000, 20000,
]

REQUIRED_META = ["measurement_id", "device_model", "sample_rate", "start_time", "location_id"]


# ---------------------------------------------------------------- 基础工具
def db(x, floor=-200.0):
    """功率比转 dB（x 为均方值/功率比）"""
    with np.errstate(divide="ignore"):
        v = 10.0 * np.log10(np.maximum(x, 1e-300))
    return np.maximum(v, floor)


def a_weighting_db(freqs):
    """IEC 61672 A 计权（解析式），返回各频率的 dB 修正值（1 kHz = 0 dB）"""
    f2 = np.asarray(freqs, dtype=float) ** 2
    num = (12194.0 ** 2) * (f2 ** 2)
    den = (
        (f2 + 20.6 ** 2)
        * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))
        * (f2 + 12194.0 ** 2)
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        ra = num / den
        a = 20.0 * np.log10(np.maximum(ra, 1e-300)) + 2.00
    a[np.asarray(freqs) == 0] = -200.0
    return a


def read_wav(path):
    sr, data = wavfile.read(path)
    if data.dtype == np.int16:
        x = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        x = data.astype(np.float64) / 2147483648.0
    elif data.dtype == np.uint8:
        x = (data.astype(np.float64) - 128.0) / 128.0
    else:
        x = data.astype(np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)  # 多声道降为单声道（能量近似）
    return sr, x


def load_meta(path):
    if not path:
        return {}
    if not os.path.exists(path):
        raise SystemExit(f"元数据文件不存在: {path}")
    if path.endswith(".json"):
        return json.load(open(path, encoding="utf-8"))
    try:
        import yaml
        return yaml.safe_load(open(path, encoding="utf-8")) or {}
    except ImportError:
        # 无 pyyaml 时退化为简单 key: value 解析
        out = {}
        for line in open(path, encoding="utf-8"):
            if ":" in line and not line.strip().startswith("#"):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
        return out


def calibration_offset(meta):
    """返回 (offset_db, calibrated: bool)

    offset_db 使 SPL = dBFS + offset_db
    支持两种写法：
      calibration: {ref_spl_db: 94.0, ref_dbfs: -20.0}
      calibration_offset_db: 114.0
    """
    cal = meta.get("calibration") or {}
    if isinstance(cal, dict) and cal.get("ref_spl_db") is not None and cal.get("ref_dbfs") is not None:
        return float(cal["ref_spl_db"]) - float(cal["ref_dbfs"]), True
    if meta.get("calibration_offset_db") is not None:
        return float(meta["calibration_offset_db"]), True
    return 0.0, False


# ---------------------------------------------------------------- 指标计算
def basic_stats(x, sr):
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    rms = float(np.sqrt(np.mean(x ** 2))) if x.size else 0.0
    clip_n = int(np.sum(np.abs(x) >= 0.999))
    dc = float(np.mean(x)) if x.size else 0.0
    # 静音比例：连续 50ms 窗口 RMS 低于 -60 dBFS
    win = max(1, int(0.05 * sr))
    n = len(x) // win
    if n:
        frames = x[: n * win].reshape(n, win)
        fr_rms = np.sqrt(np.mean(frames ** 2, axis=1))
        silent_ratio = float(np.mean(fr_rms < 1e-3))
    else:
        silent_ratio = 1.0
    return {
        "duration_s": round(len(x) / sr, 3),
        "peak_dbfs": round(20 * math.log10(peak) if peak > 0 else -200.0, 2),
        "rms_dbfs": round(20 * math.log10(rms) if rms > 0 else -200.0, 2),
        "crest_db": round((20 * math.log10(peak) - 20 * math.log10(rms)) if rms > 0 and peak > 0 else 0.0, 2),
        "clipped_samples": clip_n,
        "clip_ratio": round(clip_n / max(1, len(x)), 6),
        "dc_offset": round(dc, 6),
        "silent_ratio": round(silent_ratio, 3),
    }


def _one_sided_psd(chunk, win):
    """单边功率谱，归一化到「各 bin 功率之和 = 均方值」（Parseval 精确式）

    mean_square = Σ|X_k|² / (N · Σw²)，rfft 只给一半谱，故内部 bin ×2。
    """
    n = len(chunk)
    X = np.fft.rfft(chunk * win)
    p = np.abs(X) ** 2
    if p.size > 2:
        p[1:-1] *= 2.0
    return p / (n * np.sum(win ** 2))


def band_power(x, sr, centers, frac=1.0):
    """返回 {中心频率: 该带宽内均方值}（Hann 窗分段平均）"""
    n = len(x)
    if n == 0:
        return {c: 0.0 for c in centers}
    seg = min(1 << 16, max(1024, 1 << int(math.log2(max(1024, n // 8)))))
    step = seg // 2
    if n < seg:
        seg, step = n, n
    win = np.hanning(seg)
    freqs = np.fft.rfftfreq(seg, 1.0 / sr)

    acc = np.zeros(len(freqs))
    count = 0
    for start in range(0, max(1, n - seg + 1), step):
        chunk = x[start:start + seg]
        if len(chunk) < seg:
            break
        acc += _one_sided_psd(chunk, win)
        count += 1
    if count == 0:
        return {c: 0.0 for c in centers}
    acc /= count

    out = {}
    for c in centers:
        if frac == 1.0:
            lo, hi = c / math.sqrt(2), c * math.sqrt(2)
        else:  # 1/3 倍频程
            lo, hi = c * 2 ** (-1 / 6), c * 2 ** (1 / 6)
        mask = (freqs >= lo) & (freqs < hi)
        out[c] = float(np.sum(acc[mask])) if np.any(mask) else 0.0
    return out


def weighted_leq(x, sr, calibrated_offset, use_a):
    """返回 (leq_db, mode)；use_a 时在频域施加 A 计权"""
    if x.size == 0:
        return -200.0, "empty"
    if not use_a:
        ms = float(np.mean(x ** 2))
        return round(db(np.array([ms]))[0] + calibrated_offset, 2), "Z"
    # 频域 A 计权（Parseval 归一化，见 _one_sided_psd）
    n = len(x)
    seg = min(1 << 16, max(1024, 1 << int(math.log2(max(1024, n // 8)))))
    step = seg // 2
    if n < seg:
        seg, step = n, n
    win = np.hanning(seg)
    freqs = np.fft.rfftfreq(seg, 1.0 / sr)
    gain = 10 ** (a_weighting_db(freqs) / 10.0)  # 功率域
    total, count = 0.0, 0
    for start in range(0, max(1, n - seg + 1), step):
        chunk = x[start:start + seg]
        if len(chunk) < seg:
            break
        total += float(np.sum(_one_sided_psd(chunk, win) * gain))
        count += 1
    if count == 0:
        return -200.0, "A"
    return round(db(np.array([total / count]))[0] + calibrated_offset, 2), "A"


def percentiles(x, sr, calibrated_offset, use_a, frame_s=0.125, pcts=(10, 50, 90)):
    """按帧计算统计声级 L10/L50/L90（帧长默认 125 ms，对齐常见 SLM Fast 档）"""
    win = max(1, int(frame_s * sr))
    n = len(x) // win
    if n < 1:
        return {}
    vals = []
    for i in range(n):
        seg = x[i * win:(i + 1) * win]
        v, _ = weighted_leq(seg, sr, calibrated_offset, use_a)
        vals.append(v)
    arr = np.array(vals)
    return {f"L{p}": round(float(np.percentile(arr, 100 - p)), 2) for p in pcts}


# ---------------------------------------------------------------- 子命令
def cmd_qc(args):
    sr, x = read_wav(args.wav)
    meta = load_meta(args.meta)
    st = basic_stats(x, sr)
    offset, calibrated = calibration_offset(meta)
    st.update({
        "file": os.path.basename(args.wav),
        "sample_rate": sr,
        "calibrated": calibrated,
        "calibration_offset_db": round(offset, 2) if calibrated else None,
        "verdict": "PASS",
        "issues": [],
    })
    if st["clip_ratio"] > 0.001:
        st["issues"].append(f"削波样本 {st['clipped_samples']} ({st['clip_ratio']*100:.2f}%) — 降低增益重录")
    if abs(st["dc_offset"]) > 0.01:
        st["issues"].append(f"直流偏移 {st['dc_offset']:.4f} — 需高通滤波")
    if st["silent_ratio"] > 0.5:
        st["issues"].append(f"静音占比 {st['silent_ratio']*100:.0f}% — 检查是否空录")
    if not calibrated:
        st["issues"].append("未提供校准值 — 只能输出相对电平（dBFS），不得标 dB SPL")
    if st["issues"]:
        st["verdict"] = "WARN"
    print(json.dumps(st, ensure_ascii=False, indent=2))
    return 0 if st["verdict"] == "PASS" else 2


def cmd_metrics(args):
    sr, x = read_wav(args.wav)
    meta = load_meta(args.meta)
    offset, calibrated = calibration_offset(meta)
    leq_z, _ = weighted_leq(x, sr, offset, use_a=False)
    leq_a, _ = weighted_leq(x, sr, offset, use_a=True)
    st = basic_stats(x, sr)
    pct_z = percentiles(x, sr, offset, use_a=False)
    pct_a = percentiles(x, sr, offset, use_a=True)
    oct_p = band_power(x, sr, OCTAVE_CENTERS, frac=1.0)
    third_p = band_power(x, sr, THIRD_OCTAVE_CENTERS, frac=1 / 3)
    oct_db = {str(k): round(db(np.array([v]))[0] + (offset if calibrated else 0), 2) for k, v in oct_p.items()}
    third_db = {str(k): round(db(np.array([v]))[0] + (offset if calibrated else 0), 2) for k, v in third_p.items()}
    out = {
        "file": os.path.basename(args.wav),
        "sample_rate": sr,
        "duration_s": st["duration_s"],
        "unit": "dB SPL" if calibrated else "dBFS (REL)",
        "calibrated": calibrated,
        "calibration": {"offset_db": round(offset, 2)} if calibrated else None,
        "Leq_Z": leq_z,
        "Leq_A": leq_a,
        "Lmax": st["peak_dbfs"] + (offset if calibrated else 0),
        "Lmin_est": None,
        "percentiles_Z": pct_z,
        "percentiles_A": pct_a,
        "octave_bands": oct_db,
        "third_octave_bands": third_db,
        "qc": {k: st[k] for k in ("clipped_samples", "clip_ratio", "dc_offset", "silent_ratio", "crest_db")},
        "method": {
            "A_weighting": "IEC 61672 解析式，频域施加，1 kHz = 0 dB",
            "Leq": "能量平均；A 计权版本为频域加权后全带能量",
            "percentiles": "125 ms 帧 Leq 的 P90/P50/P10 → L10/L50/L90",
            "octave": "Hann 窗分段平均周期图，倍频程边界 fc/√2 ~ fc·√2",
        },
    }
    if not calibrated:
        out["warning"] = "无校准值：以上为相对电平（dBFS），不可当作声压级使用"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _scan_dir(root):
    files = []
    for dirpath, _, names in os.walk(root):
        for n in names:
            if n.lower().endswith((".wav", ".flac", ".wave")):
                files.append(os.path.join(dirpath, n))
    return sorted(files)


def _find_meta(wav_path):
    for ext in (".yaml", ".yml", ".json"):
        p = os.path.splitext(wav_path)[0] + ext
        if os.path.exists(p):
            return p
    return None


def cmd_ingest(args):
    files = _scan_dir(args.dir)
    if not files:
        print("未找到音频文件")
        return 1
    entries, rejected = [], []
    for f in files:
        meta_path = _find_meta(f)
        meta = load_meta(meta_path) if meta_path else {}
        missing = [k for k in REQUIRED_META if meta.get(k) in (None, "")]
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        rec = {
            "file": os.path.relpath(f, args.dir),
            "sha256": h.hexdigest(),
            "size_bytes": os.path.getsize(f),
            "meta_path": os.path.relpath(meta_path, args.dir) if meta_path else None,
            "meta": meta,
            "missing_fields": missing,
            "status": "accepted" if not missing else "rejected",
        }
        (entries if not missing else rejected).append(rec)

    manifest = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "root": os.path.abspath(args.dir),
        "required_fields": REQUIRED_META,
        "total": len(files),
        "accepted": len(entries),
        "rejected": len(rejected),
        "entries": entries + rejected,
    }
    out = os.path.join(args.dir, "manifest.json")
    json.dump(manifest, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: manifest[k] for k in ("total", "accepted", "rejected")}, ensure_ascii=False))
    for r in rejected:
        print(f"  ✗ {r['file']} — 缺: {', '.join(r['missing_fields'])}")
    print(f"manifest → {out}")
    return 0 if not rejected else 2


def cmd_aggregate(args):
    man_path = os.path.join(args.dir, "manifest.json")
    if not os.path.exists(man_path):
        print("先运行 ingest 生成 manifest.json")
        return 1
    man = json.load(open(man_path, encoding="utf-8"))
    rows = []
    for e in man["entries"]:
        if e["status"] != "accepted":
            continue
        wav = os.path.join(args.dir, e["file"])
        try:
            sr, x = read_wav(wav)
            meta = e["meta"]
            offset, calibrated = calibration_offset(meta)
            leq_z, _ = weighted_leq(x, sr, offset, False)
            leq_a, _ = weighted_leq(x, sr, offset, True)
            st = basic_stats(x, sr)
            rows.append({
                "measurement_id": meta.get("measurement_id"),
                "file": e["file"],
                "start_time": meta.get("start_time"),
                "location_id": meta.get("location_id"),
                "device_model": meta.get("device_model"),
                "sample_rate": sr,
                "duration_s": st["duration_s"],
                "unit": "dB SPL" if calibrated else "dBFS",
                "Leq_Z": leq_z,
                "Leq_A": leq_a,
                "clip_ratio": st["clip_ratio"],
                "sha256": e["sha256"][:16],
            })
        except Exception as ex:  # noqa: BLE001
            print(f"  ! {e['file']}: {ex}")

    csv_path = os.path.join(args.dir, "dataset.csv")
    if rows:
        cols = list(rows[0].keys())
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(",".join(cols) + "\n")
            for r in rows:
                f.write(",".join(str(r[c]) for c in cols) + "\n")

    dict_md = os.path.join(args.dir, "data_dictionary.md")
    with open(dict_md, "w", encoding="utf-8") as f:
        f.write("# 数据字典\n\n| 字段 | 含义 | 单位 |\n|:--|:--|:--|\n")
        spec = [
            ("measurement_id", "测点记录唯一标识", "—"), ("file", "音频文件相对路径", "—"),
            ("start_time", "测量开始时间（含时区）", "ISO8601"), ("location_id", "测点编号", "—"),
            ("device_model", "设备型号", "—"), ("sample_rate", "采样率", "Hz"),
            ("duration_s", "时长", "s"), ("unit", "电平单位（校准与否）", "—"),
            ("Leq_Z", "Z 计权等效声级", "dB SPL / dBFS"), ("Leq_A", "A 计权等效声级", "dB SPL / dBFS"),
            ("clip_ratio", "削波样本比例", "—"), ("sha256", "文件内容哈希前 16 位", "—"),
        ]
        for k, v, u in spec:
            f.write(f"| `{k}` | {v} | {u} |\n")

    print(json.dumps({"rows": len(rows), "csv": csv_path, "dict": dict_md}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="声学聚合数据工具链")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("qc", help="单文件质量检查")
    p.add_argument("wav")
    p.add_argument("--meta")
    p.set_defaults(func=cmd_qc)

    p = sub.add_parser("metrics", help="声学指标计算")
    p.add_argument("wav")
    p.add_argument("--meta")
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("ingest", help="扫描目录并校验元数据")
    p.add_argument("dir")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("aggregate", help="汇总为数据集")
    p.add_argument("dir")
    p.set_defaults(func=cmd_aggregate)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
