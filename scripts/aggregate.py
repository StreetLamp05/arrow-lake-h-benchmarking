#!/usr/bin/env python3
"""Aggregate per-run measurements from results/profiling/raw/* into summary.csv
and the three figures used in the paper."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "profiling" / "raw"
OUT_DIR = ROOT / "results" / "profiling"

TIERS = ["P", "E", "LPE"]
TIER_COLORS = {"P": "#d62728", "E": "#1f77b4", "LPE": "#2ca02c"}
TIER_LABELS = {"P": "P (Lion Cove)", "E": "E (Skymont)", "LPE": "LP E (Skymont)"}

PERF_ROW = re.compile(r"^\s*([\d,]+)\s+([\w_/\-:]+)\s*$")


def parse_energy(path: Path) -> dict:
    d = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def parse_perf(path: Path) -> dict:
    """Pull instructions, cycles, cache-refs, cache-misses from perf stat output."""
    d = {}
    if not path.exists():
        return d
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = PERF_ROW.match(line)
        if m:
            val, evt = m.group(1).replace(",", ""), m.group(2)
            # strip :u suffix and PMU prefix
            evt = evt.split("/")[1] if "/" in evt else evt
            evt = evt.rstrip(":u")
            try:
                d[evt] = int(val)
            except ValueError:
                pass
    return d


def parse_stream_stdout(path: Path) -> dict:
    """Parse STREAM stdout for Copy/Scale/Add/Triad best rates."""
    d = {}
    if not path.exists():
        return d
    for line in path.read_text().splitlines():
        m = re.match(r"^(Copy|Scale|Add|Triad):\s+([\d.]+)", line)
        if m:
            d[f"stream_{m.group(1).lower()}_mbps"] = float(m.group(2))
    return d


def parse_npb_stdout(path: Path) -> dict:
    """Parse NPB stdout for Mop/s and Class."""
    d = {}
    if not path.exists():
        return d
    for line in path.read_text().splitlines():
        m = re.match(r"^\s*Mop/s total\s*=\s*(\S+)", line)
        if m:
            v = m.group(1)
            d["mops_s"] = float("nan") if v.lower() == "inf" else float(v)
        m2 = re.match(r"^\s*Class\s*=\s*(\S+)", line)
        if m2:
            d["npb_class"] = m2.group(1)
        m3 = re.match(r"^\s*Time in seconds\s*=\s*([\d.]+)", line)
        if m3:
            d["npb_time_s"] = float(m3.group(1))
    return d


def collect(pass_name: str, bench_kind: str) -> list[dict]:
    """
    pass_name: "stream_1t" | "stream_full" | "npb_1t" | "npb_full"
    bench_kind: "stream" | "npb"
    """
    pass_dir = RAW / pass_name
    if not pass_dir.exists():
        return []
    rows = []
    # layout for STREAM: stream_1t/rN/<tier>.*
    # layout for NPB:    npb_1t/<kernel>/rN/<tier>.*
    if bench_kind == "stream":
        run_dirs = sorted([d for d in pass_dir.iterdir() if d.is_dir() and d.name.startswith("r")])
        for rd in run_dirs:
            run = int(rd.name[1:])
            for t in TIERS:
                ef = rd / f"{t}.energy.txt"
                if not ef.exists():
                    continue
                row = {"pass": pass_name, "bench": "stream", "tier": t, "run": run}
                row.update({k: v for k, v in parse_energy(ef).items()})
                row.update(parse_perf(rd / f"{t}.perf.txt"))
                row.update(parse_stream_stdout(rd / f"{t}.stdout.txt"))
                rows.append(row)
    else:
        for kd in sorted(pass_dir.iterdir()):
            if not kd.is_dir():
                continue
            kernel = kd.name  # ep.B, cg.B, is.B, mg.B
            for rd in sorted([d for d in kd.iterdir() if d.is_dir() and d.name.startswith("r")]):
                run = int(rd.name[1:])
                for t in TIERS:
                    ef = rd / f"{t}.energy.txt"
                    if not ef.exists():
                        continue
                    row = {"pass": pass_name, "bench": kernel, "tier": t, "run": run}
                    row.update({k: v for k, v in parse_energy(ef).items()})
                    row.update(parse_perf(rd / f"{t}.perf.txt"))
                    row.update(parse_npb_stdout(rd / f"{t}.stdout.txt"))
                    rows.append(row)
    return rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    rows += collect("stream_1t", "stream")
    rows += collect("stream_full", "stream")
    rows += collect("npb_1t", "npb")
    rows += collect("npb_full", "npb")

    df = pd.DataFrame(rows)

    # Type coercion.
    numeric_cols = [
        "wall_seconds", "rapl_pkg_joules", "rapl_core_joules", "omp_num_threads",
        "instructions", "cycles", "cache-references", "cache-misses", "task-clock",
        "stream_copy_mbps", "stream_scale_mbps", "stream_add_mbps", "stream_triad_mbps",
        "mops_s", "npb_time_s",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Derived.
    df["ipc"] = df["instructions"] / df["cycles"]
    df["miss_rate"] = df["cache-misses"] / df["cache-references"]
    df["pkg_watts"] = df["rapl_pkg_joules"] / df["wall_seconds"]
    df["core_watts"] = df["rapl_core_joules"] / df["wall_seconds"]

    # Flag run 1 as warmup where wall >= 1.5x the median of later runs
    # in the same (pass, bench, tier, omp_num_threads) group.
    df["is_warmup"] = False
    group_cols = ["pass", "bench", "tier", "omp_num_threads"]
    for key, sub in df.groupby(group_cols):
        later = sub[sub["run"] > 1]
        if later.empty:
            continue
        med = later["wall_seconds"].median()
        r1 = sub[sub["run"] == 1]
        for idx in r1.index:
            if df.loc[idx, "wall_seconds"] >= 1.5 * med:
                df.loc[idx, "is_warmup"] = True

    summary_path = OUT_DIR / "summary.csv"
    df.to_csv(summary_path, index=False)
    print(f"[aggregate] wrote {summary_path} ({len(df)} rows, {df['is_warmup'].sum()} warmup-flagged)")

    # ---------- figures ----------
    clean = df[~df["is_warmup"]].copy()

    def means_per_tier(mask, metric):
        out = {}
        for t in TIERS:
            vals = clean[mask & (clean["tier"] == t)][metric].dropna()
            out[t] = vals.mean() if len(vals) else np.nan
        return out

    # Figure 1: bandwidth per tier (STREAM Triad, 1-thread vs full-tier)
    triad_1t = means_per_tier(clean["pass"] == "stream_1t", "stream_triad_mbps")
    triad_ft = means_per_tier(clean["pass"] == "stream_full", "stream_triad_mbps")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.arange(len(TIERS))
    w = 0.35
    ax.bar(x - w/2, [triad_1t[t] / 1000 for t in TIERS], w,
           color=[TIER_COLORS[t] for t in TIERS], alpha=0.6, edgecolor="black")
    ax.bar(x + w/2, [triad_ft[t] / 1000 for t in TIERS], w,
           color=[TIER_COLORS[t] for t in TIERS], edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels([TIER_LABELS[t] for t in TIERS])
    ax.set_ylabel("STREAM Triad bandwidth (GB/s)")
    ax.set_title("Memory bandwidth per tier: single thread vs full tier")
    ax.legend(handles=[
        Patch(facecolor="lightgray", edgecolor="black", label="1 thread"),
        Patch(facecolor="dimgray", edgecolor="black", label="full tier"),
    ], loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    for i, t in enumerate(TIERS):
        ax.text(i - w/2, triad_1t[t] / 1000 + 1, f"{triad_1t[t]/1000:.1f}", ha="center", fontsize=8)
        ax.text(i + w/2, triad_ft[t] / 1000 + 1, f"{triad_ft[t]/1000:.1f}", ha="center", fontsize=8)
    plt.tight_layout()
    fp1 = OUT_DIR / "fig_bandwidth_per_tier.pdf"
    fig.savefig(fp1)
    plt.close(fig)
    print(f"[aggregate] wrote {fp1}")

    # Figure 2: full-tier wall-time speedup per kernel, P (6t) = 1.0.
    kernels = ["ep.B", "cg.B", "is.B", "mg.B"]
    kernel_labels = ["EP (compute)", "CG (mem-latency)", "IS (sort/bw)", "MG (mixed)"]
    speedup = {t: [] for t in TIERS}
    for k in kernels:
        mask = (clean["pass"] == "npb_full") & (clean["bench"] == k)
        sub = clean[mask]
        p_wall = sub[sub["tier"] == "P"]["wall_seconds"].mean()
        for t in TIERS:
            tier_wall = sub[sub["tier"] == t]["wall_seconds"].mean()
            speedup[t].append(p_wall / tier_wall if tier_wall else np.nan)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(kernels))
    w = 0.25
    for i, t in enumerate(TIERS):
        offset = (i - 1) * w
        bars = ax.bar(x + offset, speedup[t], w, label=TIER_LABELS[t],
                      color=TIER_COLORS[t], edgecolor="black")
        for b, v in zip(bars, speedup[t]):
            if not np.isnan(v):
                ax.text(b.get_x() + b.get_width()/2, v + 0.03, f"{v:.2f}×",
                        ha="center", fontsize=8)
    ax.axhline(1.0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(kernel_labels)
    ax.set_ylabel("Speedup vs P tier (6 threads)")
    ax.set_title("Three-point performance surface: full-tier throughput per NPB kernel")
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    fp2 = OUT_DIR / "fig_three_point_surface.pdf"
    fig.savefig(fp2)
    plt.close(fig)
    print(f"[aggregate] wrote {fp2}")

    # Figure 3: energy per unit work, full-tier, each kernel
    fig, ax = plt.subplots(figsize=(8, 4.5))
    energies = {t: [] for t in TIERS}
    for k in kernels:
        mask = (clean["pass"] == "npb_full") & (clean["bench"] == k)
        sub = clean[mask]
        for t in TIERS:
            e = sub[sub["tier"] == t]["rapl_pkg_joules"].mean()
            energies[t].append(e)
    for i, t in enumerate(TIERS):
        offset = (i - 1) * w
        bars = ax.bar(x + offset, energies[t], w, label=TIER_LABELS[t],
                      color=TIER_COLORS[t], edgecolor="black")
        for b, v in zip(bars, energies[t]):
            if not np.isnan(v):
                ax.text(b.get_x() + b.get_width()/2, v + max(energies["LPE"])*0.01,
                        f"{v:.0f}J", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(kernel_labels)
    ax.set_ylabel("Package energy per run (J)")
    ax.set_title("Energy per run: each tier at full thread count")
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    fp3 = OUT_DIR / "fig_energy_per_tier.pdf"
    fig.savefig(fp3)
    plt.close(fig)
    print(f"[aggregate] wrote {fp3}")

    print()
    print("=== Headline means (full-tier, warmup-flagged runs excluded) ===")
    for k in ["ep.B", "cg.B", "is.B", "mg.B"]:
        print(f"\n{k}:")
        sub = clean[(clean["pass"] == "npb_full") & (clean["bench"] == k)]
        for t in TIERS:
            s = sub[sub["tier"] == t]
            if not s.empty:
                print(f"  {t:3s} n={len(s)}  wall={s['wall_seconds'].mean():8.2f}s  "
                      f"mops={s['mops_s'].mean():8.1f}  pkg={s['rapl_pkg_joules'].mean():7.1f}J  "
                      f"W={s['pkg_watts'].mean():5.1f}  ipc={s['ipc'].mean():.2f}")

    print("\n=== STREAM Triad means ===")
    for pn in ["stream_1t", "stream_full"]:
        print(f"\n{pn}:")
        sub = clean[clean["pass"] == pn]
        for t in TIERS:
            s = sub[sub["tier"] == t]
            if not s.empty:
                gb = s["stream_triad_mbps"].mean() / 1000
                pkg = s["rapl_pkg_joules"].mean()
                w = s["pkg_watts"].mean()
                print(f"  {t:3s} n={len(s)}  triad={gb:6.1f} GB/s  pkg={pkg:6.2f}J  W={w:5.1f}")


if __name__ == "__main__":
    main()
