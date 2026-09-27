#!/usr/bin/env python3
"""Re-derive every slurm-scheduler-lab number the profile README quotes.

The profile's first finding quotes ranges over seeds 0-9 (backfill's effect on
mean wait, each priority weight's effect, exact vs padded time limits). Those
ranges come from a loop over seeds, not from one command in the lab's README,
so without this script they could not be reproduced by anyone else.

Everything goes through the `schedlab` CLI, never the library, because the CLI
applies the configuration the numbers were published under (demo weights, Fair
Tree fairshare, Slurm's default SchedulerParameters, conservative backfill).

Usage:
    python scripts/reproduce_scheduler_claims.py --schedlab /path/to/schedlab

Standard library only. The output lines are what claims.toml's `reproduce`
claims match against; change the wording here and there together.
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys

JOBS = "300"
SEEDS = range(10)
FACTORS = ("age", "fairshare", "jobsize", "qos")


def run(schedlab: str, *args: str) -> str:
    # A CLI error must fail the check, not read as a missing number, and the
    # log must say why: the likeliest failure is a schedlab from an older
    # branch rejecting a flag, and that reason is only in schedlab's stderr.
    # check=True would raise with the exit status alone.
    cmd = [schedlab, *args]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except OSError as err:
        sys.exit(f"could not run {schedlab}: {err}")
    if proc.returncode != 0:
        sys.exit(f"`{' '.join(cmd)}` exited {proc.returncode}:\n{proc.stderr.rstrip()}")
    return proc.stdout


def compare_backfill(schedlab: str, seed: int) -> dict[str, dict[str, float]]:
    """Parse the OFF and ON legs of `--compare-backfill`."""
    out = run(schedlab, "--compare-backfill", "--jobs", JOBS, "--seed", str(seed))
    legs: dict[str, dict[str, float]] = {}
    leg = ""
    for line in out.splitlines():
        if line.startswith("backfill OFF"):
            leg = "off"
        elif line.startswith("backfill ON"):
            leg = "on"
        elif leg:
            m = re.match(r"\s+(cpu utilization|mean wait)\s+([\d.]+)", line)
            if m:
                legs.setdefault(leg, {})[m.group(1)] = float(m.group(2))
    if set(legs) != {"off", "on"}:
        sys.exit(f"could not parse --compare-backfill output for seed {seed}")
    return legs


def sweep_mean_waits(schedlab: str, factor: str, seed: int) -> list[float]:
    out = run(schedlab, "--sweep", factor, "--jobs", JOBS, "--seed", str(seed))
    waits = [float(w) for w in re.findall(r"mean wait\s+([\d.]+) min", out)]
    if len(waits) != 4:
        sys.exit(f"expected 4 sweep rows for {factor} seed {seed}, got {len(waits)}")
    return waits


def seed_table(schedlab: str, *extra: str) -> dict[int, tuple[float, float]]:
    """Per-seed (utilization %, mean wait min) from `--seeds 10`."""
    out = run(schedlab, "--jobs", JOBS, "--seed", "0", "--seeds", str(len(SEEDS)), *extra)
    rows: dict[int, tuple[float, float]] = {}
    for line in out.splitlines():
        m = re.match(r"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s", line)
        if m:
            rows[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    if sorted(rows) != list(SEEDS):
        sys.exit(f"could not parse the --seeds table ({extra or 'default'})")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--schedlab", default="schedlab", help="path to the schedlab CLI")
    schedlab = parser.parse_args().schedlab

    headline = compare_backfill(schedlab, 5)
    print(
        "compare-backfill seed 5: cpu utilization "
        f"{headline['off']['cpu utilization']:.1f}% -> {headline['on']['cpu utilization']:.1f}%, "
        f"mean wait {headline['off']['mean wait']:.1f} -> {headline['on']['mean wait']:.1f} min"
    )

    cuts = []
    for seed in SEEDS:
        legs = headline if seed == 5 else compare_backfill(schedlab, seed)
        cuts.append(legs["off"]["mean wait"] / legs["on"]["mean wait"])
    print(
        f"backfill mean-wait cut, seeds 0-9: {min(cuts):.1f}x-{max(cuts):.1f}x (median {statistics.median(cuts):.2f}x)"
    )

    # max/min mean wait across weights 0, 1e3, 1e4, 1e5 for one factor, the
    # other weights left at the CLI's demo values. A ratio, not a difference,
    # so seeds with long and short queues weigh the same.
    for factor in FACTORS:
        ratios = []
        for seed in SEEDS:
            waits = sweep_mean_waits(schedlab, factor, seed)
            ratios.append(max(waits) / min(waits))
        print(
            f"weight sweep max/min mean wait, seeds 0-9: {factor} "
            f"{min(ratios):.2f}x-{max(ratios):.2f}x (median {statistics.median(ratios):.2f}x)"
        )

    padded = seed_table(schedlab)
    exact = seed_table(schedlab, "--time-limit-model", "exact")
    wait_up = sum(exact[s][1] > padded[s][1] for s in SEEDS)
    util_up = sum(exact[s][0] > padded[s][0] for s in SEEDS)
    print(
        "exact vs padded time limits, seeds 0-9: "
        f"mean wait higher on {wait_up}/10, cpu utilization higher on {util_up}/10"
    )


if __name__ == "__main__":
    main()
