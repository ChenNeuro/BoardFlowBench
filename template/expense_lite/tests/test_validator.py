import unittest

from expense_lite import validator


class ValidatorTest(unittest.TestCase):
    def test_validate_expense_normalizes_record(self) -> None:
        record = {
            "date": "2026-01-03",
            "description": " Notebook ",
            "category": "office",
            "amount": 12.5,
        }

        self.assertEqual(
            validator.validate_expense(record),
            {
                "date": "2026-01-03",
                "description": "Notebook",
                "category": "office",
                "amount": 12.5,
            },
        )

    def test_validate_expense_rejects_missing_fields(self) -> None:
        with self.assertRaises(ValueError):
            validator.validate_expense({"date": "2026-01-03"})

    def test_validate_expense_rejects_non_numeric_amount(self) -> None:
        with self.assertRaises(ValueError):
            validator.validate_expense(
                {
                    "date": "2026-01-03",
                    "description": "Notebook",
                    "category": "office",
                    "amount": "12.50",
                }
            )


if __name__ == "__main__":
    unittest.main()
