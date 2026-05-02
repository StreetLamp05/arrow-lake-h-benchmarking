#!/usr/bin/env python3
"""Aggregate results/td/raw/<workload>_<tier>.log files into results/td/summary.csv
and results/td/fig_validity_heatmap.pdf.

Each raw-log line: <timestamp>\t<cpu>\t<raw_hex>\t<valid>\t<class_id>
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "td" / "raw"
OUT = ROOT / "results" / "td"

WORKLOADS = ["idle", "ep.B", "cg.B", "stream"]
TIERS = ["P", "E", "LPE"]


def parse_log(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        ts, cpu, raw_hex, valid, class_id = parts
        try:
            rows.append({
                "ts": float(ts),
                "cpu": int(cpu),
                "raw_hex": raw_hex,
                "valid": int(valid),
                "class_id": int(class_id),
            })
        except ValueError:
            continue
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n_samples": 0, "valid_rate": float("nan"),
                "modal_class_id": -1, "modal_class_valid": -1,
                "class_transitions": 0, "class_stability": float("nan")}
    n = len(df)
    valid_rate = df["valid"].mean()
    modal_all = Counter(df["class_id"]).most_common(1)[0][0]
    vdf = df[df["valid"] == 1]
    modal_valid = Counter(vdf["class_id"]).most_common(1)[0][0] if len(vdf) else -1
    transitions = int((df["class_id"].diff() != 0).sum() - 1) if n > 1 else 0
    stability = 1 - transitions / (n - 1) if n > 1 else float("nan")
    return {
        "n_samples": n,
        "valid_rate": valid_rate,
        "modal_class_id": modal_all,
        "modal_class_valid": modal_valid,
        "class_transitions": transitions,
        "class_stability": stability,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    validity_matrix = np.full((len(WORKLOADS), len(TIERS)), np.nan)

    for i, workload in enumerate(WORKLOADS):
        for j, tier in enumerate(TIERS):
            path = RAW / f"{workload}_{tier}.log"
            df = parse_log(path)
            s = summarize(df)
            row = {"workload": workload, "tier": tier, **s}
            rows.append(row)
            validity_matrix[i, j] = s["valid_rate"]
            print(f"{workload:8s} {tier:3s} n={s['n_samples']:4d}  "
                  f"valid_rate={s['valid_rate']:.2%}  "
                  f"modal_class(all)={s['modal_class_id']}  "
                  f"modal_class(valid)={s['modal_class_valid']}  "
                  f"stability={s['class_stability']:.2%}")

    summary_path = OUT / "summary.csv"
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    print(f"\n[td_analyze] wrote {summary_path}")

    fig, ax = plt.subplots(figsize=(6, 4))
    # Convert NaN to 0 for visualization but annotate with N/A.
    disp = np.where(np.isnan(validity_matrix), 0, validity_matrix)
    im = ax.imshow(disp, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(TIERS)))
    ax.set_xticklabels(TIERS)
    ax.set_yticks(range(len(WORKLOADS)))
    ax.set_yticklabels(WORKLOADS)
    ax.set_xlabel("Tier")
    ax.set_ylabel("Workload")
    ax.set_title("IA32_THREAD_FEEDBACK_CHAR Valid-bit rate\n(fraction of MSR samples with Valid=1)")
    for i in range(len(WORKLOADS)):
        for j in range(len(TIERS)):
            v = validity_matrix[i, j]
            txt = "N/A" if np.isnan(v) else f"{v:.0%}"
            ax.text(j, i, txt, ha="center", va="center",
                    color="black" if not np.isnan(v) and 0.3 < v < 0.7 else "white", fontsize=11)
    fig.colorbar(im, ax=ax, label="Valid-bit fraction")
    plt.tight_layout()
    fig_path = OUT / "fig_validity_heatmap.pdf"
    fig.savefig(fig_path)
    plt.close(fig)
    print(f"[td_analyze] wrote {fig_path}")


if __name__ == "__main__":
    main()
