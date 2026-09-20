"""coldiff: column-aware CSV diff.

Compares two CSV files on a key column and reports added, removed and
changed rows with cell-level old -> new values.
"""

from __future__ import annotations

import csv
import dataclasses
import json
import sys


@dataclasses.dataclass
class Diff:
    added: list[dict]
    removed: list[dict]
    changed: list[dict]  # {"key": k, "changes": {col: [old, new]}}

    @property
    def empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


def read_csv(path: str, delimiter: str = ",") -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        columns = list(reader.fieldnames or [])
        rows = [{k: ("" if v is None else v) for k, v in r.items()} for r in reader]
    if not columns:
        raise ValueError(f"{path}: no header row")
    return columns, rows


def diff(old: list[dict], new: list[dict], key: str, columns: list[str] | None = None):
    for row in old + new:
        if key not in row:
            raise ValueError(f"key column {key!r} missing in input")
    old_by = {r[key]: r for r in old}
    new_by = {r[key]: r for r in new}

    d = Diff(added=[], removed=[], changed=[])
    for r in new:
        if r[key] not in old_by:
            d.added.append(r)
    for r in old:
        if r[key] not in new_by:
            d.removed.append(r)
    for k in old_by:
        if k not in new_by:
            continue
        o, n = old_by[k], new_by[k]
        cols = columns if columns is not None else sorted(set(o) | set(n))
        changes = {}
        for col in cols:
            ov, nv = o.get(col, ""), n.get(col, "")
            if ov != nv:
                changes[col] = [ov, nv]
        if changes:
            d.changed.append({"key": k, "changes": changes})
    return d


def format_table(d: Diff, key: str) -> str:
    lines = []
    if d.added:
        lines.append(f"+ added ({len(d.added)}):")
        for r in d.added:
            fields = "  ".join(f"{k}={v}" for k, v in r.items() if k != key)
            lines.append(f"  + {key}={r[key]}  {fields}")
    if d.removed:
        lines.append(f"- removed ({len(d.removed)}):")
        for r in d.removed:
            fields = "  ".join(f"{k}={v}" for k, v in r.items() if k != key)
            lines.append(f"  - {key}={r[key]}  {fields}")
    if d.changed:
        lines.append(f"~ changed ({len(d.changed)}):")
        for c in d.changed:
            lines.append(f"  ~ {key}={c['key']}")
            for col, (ov, nv) in c["changes"].items():
                lines.append(f"      {col}: {ov!r} -> {nv!r}")
    if not lines:
        lines.append("no differences")
    return "\n".join(lines)


def format_json(d: Diff) -> str:
    return json.dumps(
        {"added": d.added, "removed": d.removed, "changed": d.changed},
        ensure_ascii=False, indent=2,
    )


def format_unified(d: Diff) -> str:
    lines = []
    for r in d.added:
        lines.append("+ " + ",".join(f"{k}={v}" for k, v in r.items()))
    for r in d.removed:
        lines.append("- " + ",".join(f"{k}={v}" for k, v in r.items()))
    for c in d.changed:
        for col, (ov, nv) in sorted(c["changes"].items()):
            lines.append(f"~ {c['key']}.{col}: {ov} -> {nv}")
    return "\n".join(lines)


USAGE = """coldiff 1.0.0 - column-aware CSV diff

USAGE:
    coldiff [options] OLD.csv NEW.csv

OPTIONS:
    -k, --key COL      key column (default: first column)
    -c, --columns LIST compare only these columns (comma separated)
    -f, --format F     table | json | unified (default: table)
    -d, --delimiter C  input delimiter (default ,)
    -h, --help         this help

EXIT CODES: 0 = no differences, 1 = differences found, 2 = usage error
"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    key = None
    columns = None
    fmt = "table"
    delimiter = ","
    files: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            print(USAGE)
            return 0
        if a in ("-k", "--key"):
            i += 1
            if i >= len(args):
                print("coldiff: --key needs a column", file=sys.stderr)
                return 2
            key = args[i]
        elif a in ("-c", "--columns"):
            i += 1
            if i >= len(args):
                print("coldiff: --columns needs a list", file=sys.stderr)
                return 2
            columns = [c.strip() for c in args[i].split(",")]
        elif a in ("-f", "--format"):
            i += 1
            if i >= len(args):
                print("coldiff: --format needs a value", file=sys.stderr)
                return 2
            fmt = args[i]
            if fmt not in ("table", "json", "unified"):
                print(f"coldiff: unknown format {fmt!r}", file=sys.stderr)
                return 2
        elif a in ("-d", "--delimiter"):
            i += 1
            if i >= len(args):
                print("coldiff: --delimiter needs a value", file=sys.stderr)
                return 2
            delimiter = args[i]
        else:
            files.append(a)
        i += 1

    if len(files) != 2:
        print("coldiff: exactly two CSV files required (try --help)", file=sys.stderr)
        return 2

    try:
        old_cols, old_rows = read_csv(files[0], delimiter)
        new_cols, new_rows = read_csv(files[1], delimiter)
        key_col = key or (old_cols[0] if old_cols else new_cols[0])
        d = diff(old_rows, new_rows, key_col, columns)
    except (OSError, ValueError) as e:
        print(f"coldiff: {e}", file=sys.stderr)
        return 2

    if fmt == "json":
        print(format_json(d))
    elif fmt == "unified":
        out = format_unified(d)
        if out:
            print(out)
    else:
        print(format_table(d, key_col))
    return 0 if d.empty else 1


if __name__ == "__main__":
    sys.exit(main())
