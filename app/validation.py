"""Structural safety checks on Gemini-generated SQL before it runs."""
import sqlglot
from sqlglot import exp

from app.database import get_schema


class UnsafeSQLError(Exception):
    """Raised when generated SQL fails a safety check."""


def validate_sql(sql: str) -> None:
    """Check that the SQL is a single read-only SELECT over known columns.

    Raises UnsafeSQLError if any check fails; returns normally if the SQL is safe.
    """
    # Parse with the SQLite dialect — this also rejects syntactically broken SQL.
    try:
        statements = [s for s in sqlglot.parse(sql, dialect="sqlite") if s is not None]
    except sqlglot.errors.ParseError as error:
        raise UnsafeSQLError(f"Query could not be parsed: {error}")

    # Exactly one statement 
    if len(statements) != 1:
        raise UnsafeSQLError("Only a single SQL statement is allowed.")

    statement = statements[0]

    # DROP, DELETE, INSERT, UPDATE, PRAGMA, etc. is rejected
    if not isinstance(statement, exp.Select):
        raise UnsafeSQLError("Only SELECT queries are allowed.")

    # Every table and column the query names must exist in the real schema.
    schema = get_schema()
    allowed_table = schema["table"].lower()
    allowed_columns = {column["name"].lower() for column in schema["columns"]}

    # The query may also reference aliases 
    allowed_columns |= {
        alias.alias.lower() for alias in statement.find_all(exp.Alias) if alias.alias
    }

    for table in statement.find_all(exp.Table):
        if table.name.lower() != allowed_table:
            raise UnsafeSQLError(f"Unknown table: {table.name}")

    for column in statement.find_all(exp.Column):
        if column.name.lower() not in allowed_columns:
            raise UnsafeSQLError(f"Unknown column: {column.name}")
