---
model: sonnet
---
# Compare Snapshots

Show what changed between two model snapshots saved with /snapshot.

## Arguments

$ARGUMENTS - Optional: two snapshot IDs to compare. If omitted, compares the two most recent.

Examples:
- `/diff` — compare last two snapshots
- `/diff 20260225_143000 20260227_091500` — compare specific snapshots

## Instructions

```python
import sys
sys.path.insert(0, '.')
from src.analysis.snapshot import list_snapshots, load_snapshot, diff_snapshots

snapshots = list_snapshots()

if not snapshots:
    print("No snapshots found. Use /snapshot to save one.")
else:
    print(f"Available snapshots ({len(snapshots)}):")
    for s in snapshots:
        print(f"  {s['id']}  {s['label']!r}  ({s['created_at'][:16]})")
```

If no IDs in arguments, use the two most recent snapshots.
Otherwise load the specified IDs.

```python
# Load and diff
snap_a = load_snapshot(id_a)
snap_b = load_snapshot(id_b)
result = diff_snapshots(snap_a, snap_b)
```

### Output Format

```
Comparing:
  Before: "base case" (Feb 25, 2:30pm)
  After:  "after Enterprise CAC cut" (Feb 27, 9:15am)

Changes by business line:
  Enterprise — CAC reduced ~50%
    Jun-27: $38,200 → $19,100  (-$19,100)
    Sep-27: $96,400 → $48,200  (-$48,200)
  [lines with no changes: omit]

Total CAC-Adjusted GM (changed months only):
  Month       Before       After        Delta
  May-27    $143,200    $170,100     +$26,900
  Jun-27    $184,500    $219,700     +$35,200
  ...

Breakeven ($175k):
  Before: Jun-27
  After:  May-27  (1 month earlier)
```

If nothing changed between snapshots, say so.
Only show months where total_gm_adj delta is non-zero.
