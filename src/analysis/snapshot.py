"""Model snapshot and diff utilities.

Snapshots capture key model outputs (CAC-adjusted GM by line and month,
breakeven month) so you can compare before/after a change.

Storage: ~/.fpa-agent/snapshots/<timestamp>.json
"""

import json
import os
from datetime import datetime
from typing import Any

SNAPSHOT_DIR = os.path.expanduser("~/.fpa-agent/snapshots")


def save_snapshot(
    label: str,
    spreadsheet_id: str,
    spreadsheet_title: str,
    metrics: dict[str, Any],
) -> str:
    """Save a snapshot of model metrics to disk.

    Args:
        label: Human-readable label (e.g. "base case", "after Enterprise CAC cut").
        spreadsheet_id: The spreadsheet ID.
        spreadsheet_title: The spreadsheet title.
        metrics: Dict containing:
            - months: list of month strings (e.g. ["Mar'26", "Apr'26", ...])
            - by_line: {line_name: {rev, cogs, cac, gm_adj}} — each a list of floats
            - total_gm_adj: list of floats (sum across all lines)
            - breakeven: str | None — e.g. "Jun-27"
            - breakeven_threshold: float — e.g. 175000

    Returns:
        Path to the saved snapshot file.
    """
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
    snapshot = {
        "id": snapshot_id,
        "label": label,
        "created_at": datetime.now().isoformat(),
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_title": spreadsheet_title,
        "metrics": metrics,
    }

    path = os.path.join(SNAPSHOT_DIR, f"{snapshot_id}.json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return path


def list_snapshots() -> list[dict[str, Any]]:
    """List all saved snapshots, newest first.

    Returns:
        List of dicts with: id, label, created_at, spreadsheet_title, path.
    """
    if not os.path.exists(SNAPSHOT_DIR):
        return []

    snapshots = []
    for fname in sorted(os.listdir(SNAPSHOT_DIR), reverse=True):
        if fname.endswith(".json"):
            path = os.path.join(SNAPSHOT_DIR, fname)
            with open(path) as f:
                data = json.load(f)
            snapshots.append({
                "id": data["id"],
                "label": data["label"],
                "created_at": data["created_at"],
                "spreadsheet_title": data.get("spreadsheet_title", ""),
                "path": path,
            })

    return snapshots


def load_snapshot(snapshot_id: str) -> dict[str, Any]:
    """Load a snapshot by ID.

    Args:
        snapshot_id: The snapshot ID (timestamp string).

    Returns:
        Full snapshot dict.
    """
    path = os.path.join(SNAPSHOT_DIR, f"{snapshot_id}.json")
    if not os.path.exists(path):
        raise ValueError(f"Snapshot '{snapshot_id}' not found in {SNAPSHOT_DIR}")
    with open(path) as f:
        return json.load(f)


def diff_snapshots(snap_a: dict[str, Any], snap_b: dict[str, Any]) -> dict[str, Any]:
    """Compute the diff between two snapshots.

    Args:
        snap_a: The "before" snapshot.
        snap_b: The "after" snapshot.

    Returns:
        Dict with:
        - from / to: snapshot metadata
        - months: list of common months
        - line_diffs: {line: {metric: {before, after, delta}}} — only changed lines
        - total_gm_adj: {before, after, delta}
        - breakeven_before / breakeven_after
    """
    months_a: list[str] = snap_a["metrics"].get("months", [])
    months_b: list[str] = snap_b["metrics"].get("months", [])
    common_months = [m for m in months_a if m in months_b]

    # Index common months in each snapshot
    idx_a = {m: i for i, m in enumerate(months_a)}
    idx_b = {m: i for i, m in enumerate(months_b)}

    def align(values: list, months: list[str]) -> list:
        """Extract values for only the common months."""
        index = {m: i for i, m in enumerate(months)}
        return [values[index[m]] if m in index and index[m] < len(values) else None for m in common_months]

    lines_a: dict = snap_a["metrics"].get("by_line", {})
    lines_b: dict = snap_b["metrics"].get("by_line", {})
    all_lines = sorted(set(lines_a.keys()) | set(lines_b.keys()))

    line_diffs: dict = {}
    for line in all_lines:
        la = lines_a.get(line, {})
        lb = lines_b.get(line, {})
        line_changed = False
        line_diff: dict = {}

        for metric in ("rev", "cogs", "cac", "gm_adj"):
            va = align(la.get(metric, []), months_a)
            vb = align(lb.get(metric, []), months_b)
            if va != vb:
                delta = [
                    round(b - a, 2) if a is not None and b is not None else None
                    for a, b in zip(va, vb)
                ]
                line_diff[metric] = {"before": va, "after": vb, "delta": delta}
                line_changed = True

        if line_changed:
            line_diffs[line] = line_diff

    total_a = align(snap_a["metrics"].get("total_gm_adj", []), months_a)
    total_b = align(snap_b["metrics"].get("total_gm_adj", []), months_b)
    total_delta = [
        round(b - a, 2) if a is not None and b is not None else None
        for a, b in zip(total_a, total_b)
    ]

    return {
        "from": {
            "id": snap_a["id"],
            "label": snap_a["label"],
            "created_at": snap_a["created_at"],
        },
        "to": {
            "id": snap_b["id"],
            "label": snap_b["label"],
            "created_at": snap_b["created_at"],
        },
        "months": common_months,
        "line_diffs": line_diffs,
        "total_gm_adj": {
            "before": total_a,
            "after": total_b,
            "delta": total_delta,
        },
        "breakeven_before": snap_a["metrics"].get("breakeven"),
        "breakeven_after": snap_b["metrics"].get("breakeven"),
        "breakeven_threshold": snap_a["metrics"].get("breakeven_threshold", 175000),
    }
