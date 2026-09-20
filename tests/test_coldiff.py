import json
import unittest

from coldiff import diff, format_json, format_table, format_unified, read_csv


def write_csv(path: str, rows: list[list[str]]) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(",".join(r) for r in rows) + "\n")
    return path


OLD = [
    ["id", "name", "city"],
    ["1", "ali", "ankara"],
    ["2", "ayse", "izmir"],
    ["3", "mehmet", "ankara"],
]
NEW = [
    ["id", "name", "city"],
    ["2", "ayse", "istanbul"],
    ["3", "mehmet", "ankara"],
    ["4", "zeynep", "bursa"],
]


class TestDiff(unittest.TestCase):
    def setUp(self):
        self.old_path = write_csv("/tmp/coldiff-old.csv", OLD)
        self.new_path = write_csv("/tmp/coldiff-new.csv", NEW)
        _, old_rows = read_csv(self.old_path)
        _, new_rows = read_csv(self.new_path)
        self.d = diff(old_rows, new_rows, "id")

    def test_classification(self):
        self.assertEqual([r["id"] for r in self.d.added], ["4"])
        self.assertEqual([r["id"] for r in self.d.removed], ["1"])
        self.assertEqual([c["key"] for c in self.d.changed], ["2"])
        self.assertEqual(self.d.changed[0]["changes"], {"city": ["izmir", "istanbul"]})

    def test_no_differences(self):
        _, rows = read_csv(self.old_path)
        d = diff(rows, rows, "id")
        self.assertTrue(d.empty)

    def test_missing_key_column(self):
        with self.assertRaises(ValueError):
            diff(OLD[1:] if isinstance(OLD[1], dict) else [{"nope": 1}],
                 [{"nope": 2}], "id")

    def test_selected_columns_only(self):
        _, old_rows = read_csv(self.old_path)
        _, new_rows = read_csv(self.new_path)
        d = diff(old_rows, new_rows, "id", columns=["name"])
        changed = [c for c in d.changed if c["changes"]]
        self.assertEqual(changed, [])  # names unchanged; city diff ignored


class TestFormats(unittest.TestCase):
    def setUp(self):
        _, old_rows = read_csv(write_csv("/tmp/coldiff-o2.csv", OLD))
        _, new_rows = read_csv(write_csv("/tmp/coldiff-n2.csv", NEW))
        self.d = diff(old_rows, new_rows, "id")

    def test_json_structure(self):
        data = json.loads(format_json(self.d))
        self.assertEqual(set(data.keys()), {"added", "removed", "changed"})
        self.assertEqual(data["changed"][0]["changes"]["city"], ["izmir", "istanbul"])

    def test_table_mentions_all_sections(self):
        table = format_table(self.d, "id")
        self.assertIn("+ added (1):", table)
        self.assertIn("- removed (1):", table)
        self.assertIn("~ changed (1):", table)
        self.assertIn("'izmir' -> 'istanbul'", table)

    def test_unified_lines(self):
        lines = format_unified(self.d).splitlines()
        self.assertTrue(any(l.startswith("+ ") for l in lines))
        self.assertTrue(any(l.startswith("- ") for l in lines))
        self.assertTrue(any(l.startswith("~ ") for l in lines))


class TestReadCsv(unittest.TestCase):
    def test_bom_and_empty(self):
        path = write_csv("/tmp/coldiff-bom.csv", [["k"], ["1"]])
        cols, rows = read_csv(path)
        self.assertEqual(cols, ["k"])
        self.assertEqual(rows, [{"k": "1"}])
        with open(path, "w", encoding="utf-8-sig") as fh:
            fh.write("k\n1\n")
        cols, rows = read_csv(path)
        self.assertEqual(cols, ["k"])


if __name__ == "__main__":
    unittest.main()
