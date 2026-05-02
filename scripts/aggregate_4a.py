#!/usr/bin/env python3
"""Aggregate results/scheduler/raw/<policy>/r<run>/metrics.txt into
results/scheduler/summary.csv and fig_policy_comparison.pdf.
Outlier rule: flag a run whose wall is >= 1.5x the median of others in the same policy.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "scheduler" / "raw"
OUT = ROOT / "results" / "scheduler"

POLICIES = ["cfs", "all_P", "pe_split", "three_way"]
POLICY_LABELS = {
    "cfs": "CFS default",
    "all_P": "All-P\n(oversubscribed)",
    "pe_split": "Two-tier\n(P + E)",
    "three_way": "Three-tier oracle\n(P + E + LP E)",
}
POLICY_COLORS = {
    "cfs": "#7f7f7f",
    "all_P": "#d62728",
    "pe_split": "#ff7f0e",
    "three_way": "#2ca02c",
}


def parse_metrics(path: Path) -> dict:
    d = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for policy in POLICIES:
        pol_dir = RAW / policy
        if not pol_dir.exists():
            continue
        for run_dir in sorted(pol_dir.iterdir()):
            if not run_dir.is_dir() or not run_dir.name.startswith("r"):
                continue
            f = run_dir / "metrics.txt"
            if not f.exists():
                continue
            m = parse_metrics(f)
            rows.append({
                "policy": policy,
                "run": int(run_dir.name[1:]),
                "wall_seconds": float(m.get("wall_seconds", "nan")),
                "rapl_pkg_joules": float(m.get("rapl_pkg_joules", "nan")),
                "rapl_core_joules": float(m.get("rapl_core_joules", "nan")),
                "cg_pin": m.get("cg_pin", ""),
                "ep_pin": m.get("ep_pin", ""),
                "io_pin": m.get("io_pin", ""),
            })

    df = pd.DataFrame(rows)

    # Outlier flag: run's wall time >= 1.5x median of other runs in the same policy.
    df["is_outlier"] = False
    for p in POLICIES:
        sub = df[df["policy"] == p]
        if len(sub) < 3:
            continue
        for idx in sub.index:
            others = sub.drop(idx)
            med = others["wall_seconds"].median()
            if df.loc[idx, "wall_seconds"] >= 1.5 * med:
                df.loc[idx, "is_outlier"] = True

    df["pkg_watts"] = df["rapl_pkg_joules"] / df["wall_seconds"]

    summary_path = OUT / "summary.csv"
    df.to_csv(summary_path, index=False)
    print(f"[aggregate_4a] wrote {summary_path} ({len(df)} rows, "
          f"{df['is_outlier'].sum()} outlier-flagged)")

    clean = df[~df["is_outlier"]].copy()
    print()
    print("=== Policy means (outliers excluded) ===")
    print(f"{'policy':<11} {'n':<3} {'wall_s':>10} {'wall_sd':>8} "
          f"{'pkg_J':>9} {'pkg_sd':>8} {'watts':>6}")
    for p in POLICIES:
        s = clean[clean["policy"] == p]
        if s.empty:
            continue
        print(f"{p:<11} {len(s):<3} "
              f"{s['wall_seconds'].mean():>10.2f} {s['wall_seconds'].std():>8.2f} "
              f"{s['rapl_pkg_joules'].mean():>9.1f} {s['rapl_pkg_joules'].std():>8.1f} "
              f"{s['pkg_watts'].mean():>6.1f}")

    # Normalized-to-CFS comparisons
    cfs_wall = clean[clean["policy"] == "cfs"]["wall_seconds"].mean()
    cfs_pkg = clean[clean["policy"] == "cfs"]["rapl_pkg_joules"].mean()
    print()
    print("=== Relative to CFS baseline (negative = better) ===")
    for p in POLICIES:
        s = clean[clean["policy"] == p]
        if s.empty: continue
        dwall = (s["wall_seconds"].mean() - cfs_wall) / cfs_wall * 100
        dpkg = (s["rapl_pkg_joules"].mean() - cfs_pkg) / cfs_pkg * 100
        print(f"  {p:<11} wall: {dwall:+6.2f}%   pkg: {dpkg:+6.2f}%")

    # ---------- figure ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    x = np.arange(len(POLICIES))

    wall_means, wall_sds, pkg_means, pkg_sds, colors, labels = [], [], [], [], [], []
    for p in POLICIES:
        s = clean[clean["policy"] == p]
        wall_means.append(s["wall_seconds"].mean())
        wall_sds.append(s["wall_seconds"].std())
        pkg_means.append(s["rapl_pkg_joules"].mean())
        pkg_sds.append(s["rapl_pkg_joules"].std())
        colors.append(POLICY_COLORS[p])
        labels.append(POLICY_LABELS[p])

    bars1 = ax1.bar(x, wall_means, yerr=wall_sds, capsize=4,
                    color=colors, edgecolor="black")
    ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("Wall time (s)")
    ax1.set_title("Time to complete mixed workload\n(6×cg.B + 4×ep.B + 2×stress-ng I/O)")
    ax1.grid(True, axis="y", alpha=0.3)
    for b, v in zip(bars1, wall_means):
        ax1.text(b.get_x() + b.get_width()/2, v + 1.5, f"{v:.1f}s",
                 ha="center", fontsize=9)

    bars2 = ax2.bar(x, pkg_means, yerr=pkg_sds, capsize=4,
                    color=colors, edgecolor="black")
    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("Package energy (J)")
    ax2.set_title("Total energy over the run\n(Intel RAPL package domain)")
    ax2.grid(True, axis="y", alpha=0.3)
    for b, v in zip(bars2, pkg_means):
        ax2.text(b.get_x() + b.get_width()/2, v + 20, f"{v:.0f}J",
                 ha="center", fontsize=9)

    plt.tight_layout()
    fp = OUT / "fig_policy_comparison.pdf"
    fig.savefig(fp)
    plt.close(fig)
    print(f"[aggregate_4a] wrote {fp}")


if __name__ == "__main__":
    main()
