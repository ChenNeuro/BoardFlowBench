import unittest

from expense_lite import report


class ReportTest(unittest.TestCase):
    def test_render_markdown_uses_stable_totals(self) -> None:
        rendered = report.render_markdown(
            {
                "2026-01": {"office": 20.0, "travel": 44.0},
                "2026-02": {"meals": 38.25},
            }
        )

        self.assertIn("# Expense Report\n", rendered)
        self.assertIn("## 2026-01\n", rendered)
        self.assertIn("- office: $20.00\n", rendered)
        self.assertIn("- Total: $64.00\n", rendered)
        self.assertTrue(rendered.endswith("Grand total: $102.25\n"))


if __name__ == "__main__":
    unittest.main()
