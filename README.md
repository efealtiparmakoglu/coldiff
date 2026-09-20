# coldiff

**Column-aware CSV diff — added / removed / changed rows with cell-level old → new values.**

[![CI](https://github.com/efealtiparmakoglu/coldiff/actions/workflows/ci.yml/badge.svg)](https://github.com/efealtiparmakoglu/coldiff/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)

```
$ coldiff -k id old.csv new.csv
+ added (1):
  + id=4  name=zeynep  city=bursa
- removed (1):
  - id=1  name=ali  city=ankara
~ changed (1):
  ~ id=2
      city: 'izmir' -> 'istanbul'
```

Line-based diff tools mangle CSVs; `coldiff` understands rows and columns.
Rows are matched on a key column, and only genuinely changed cells are
reported — with their old and new values side by side.

## Why coldiff

- **Row matching on a key column.** Reordered rows are not changes.
- **Cell-level reporting.** One changed cell = one `old -> new` line, not a
  whole-row blob.
- **Column selection.** `--columns name,city` compares a subset and ignores
  noise columns (timestamps, counters).
- **Three output formats.** Aligned table for humans, JSON for scripts,
  unified for quick scans.
- **Zero dependencies.** Python 3.9+ standard library only.

## Usage

```sh
coldiff -k id old.csv new.csv
coldiff -k email --columns name,plan users_old.csv users_new.csv -f json
coldiff -d ';' a.csv b.csv
```

Exit codes: 0 no differences, 1 differences found, 2 usage/input error —
diff-friendly in CI.

## Development

```sh
python3 -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
