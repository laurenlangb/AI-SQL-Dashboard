"""Unit tests for the sqlglot-based SQL safety validator."""
import unittest
from unittest.mock import patch

from app.validation import UnsafeSQLError, validate_sql


TEST_SCHEMA = {
    "table": "offers",
    "columns": [
        {"name": "id", "type": "INTEGER"},
        {"name": "state", "type": "TEXT"},
        {"name": "offer_amount", "type": "REAL"},
        {"name": "created_at", "type": "TEXT"},
    ],
}


class ValidateSQLTests(unittest.TestCase):
    def setUp(self):
        self.schema_patcher = patch("app.validation.get_schema", return_value=TEST_SCHEMA)
        self.schema_patcher.start()
        self.addCleanup(self.schema_patcher.stop)

    def test_allows_safe_select_shapes(self):
        safe_queries = [
            "SELECT id, state FROM offers WHERE offer_amount > 100",
            "select * from OFFERS",
            "SELECT COUNT(*) AS total FROM offers ORDER BY total",
        ]

        for sql in safe_queries:
            with self.subTest(sql=sql):
                self.assertIsNone(validate_sql(sql))

    def test_rejects_syntactically_invalid_sql(self):
        with self.assertRaisesRegex(UnsafeSQLError, "could not be parsed"):
            validate_sql("SELECT FROM WHERE")

    def test_rejects_multiple_statements(self):
        with self.assertRaisesRegex(UnsafeSQLError, "single SQL statement"):
            validate_sql("SELECT id FROM offers; DROP TABLE offers;")

    def test_rejects_non_select_statements(self):
        unsafe_queries = [
            "DELETE FROM offers WHERE id = 1",
            "UPDATE offers SET state = 'NY' WHERE id = 1",
            "INSERT INTO offers (id, state) VALUES (1, 'NY')",
        ]

        for sql in unsafe_queries:
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(UnsafeSQLError, "Only SELECT"):
                    validate_sql(sql)

    def test_rejects_unknown_schema_references(self):
        invalid_queries = [
            ("SELECT id FROM users", "Unknown table: users"),
            ("SELECT secret_margin FROM offers", "Unknown column: secret_margin"),
            ("SELECT offers.secret_margin FROM offers", "Unknown column: secret_margin"),
        ]

        for sql, error in invalid_queries:
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(UnsafeSQLError, error):
                    validate_sql(sql)


if __name__ == "__main__":
    unittest.main()
