import unittest

from expense_lite import parser


class DateParserTest(unittest.TestCase):
    def test_normalize_accepts_hyphen_date(self) -> None:
        self.assertEqual(parser.normalize_date("2026-01-03"), "2026-01-03")

    def test_normalize_accepts_slash_date(self) -> None:
        self.assertEqual(parser.normalize_date("2026/01/03"), "2026-01-03")

    def test_normalize_strips_whitespace_from_slash_date(self) -> None:
        self.assertEqual(parser.normalize_date(" 2026/01/03 "), "2026-01-03")

    def test_normalize_rejects_bad_date(self) -> None:
        with self.assertRaises(ValueError):
            parser.normalize_date("01-03-2026")

    def test_load_expenses_json_reads_records(self) -> None:
        records = parser.load_expenses_json("demo_repo_template/data/sample_expenses.json")
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["description"], "Notebook")


if __name__ == "__main__":
    unittest.main()
