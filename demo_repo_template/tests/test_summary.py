import unittest

from expense_lite import summary


class SummaryTest(unittest.TestCase):
    def test_monthly_summary_groups_by_month_and_category(self) -> None:
        expenses = [
            {"date": "2026-01-03", "category": "office", "amount": 12.5},
            {"date": "2026-01-17", "category": "travel", "amount": 44.0},
            {"date": "2026-01-20", "category": "office", "amount": 7.5},
            {"date": "2026-02-02", "category": "meals", "amount": 38.25},
        ]

        self.assertEqual(
            summary.monthly_summary(expenses),
            {
                "2026-01": {"office": 20.0, "travel": 44.0},
                "2026-02": {"meals": 38.25},
            },
        )


if __name__ == "__main__":
    unittest.main()
