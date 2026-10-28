import re
from typing import Tuple, Optional
import sqlparse
from sqlparse.sql import Statement, TokenList, Token
from sqlparse.tokens import DDL, DML, Keyword

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "REPLACE", "GRANT", "REVOKE", "PRAGMA", "ATTACH", "DETACH", "EXEC",
    "EXECUTE", "CALL", "MERGE", "UPSERT", "VACUUM", "REINDEX", "LOCK",
    "UNLOCK", "SHUTDOWN", "KILL", "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE"
}

ALLOWED_ROOT_TYPES = {"SELECT", "UNKNOWN"} # 'WITH' often parses as UNKNOWN in some sqlparse versions

class SQLValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class SQLValidator:
    """
    Validates SQL queries against strict read-only security rules.
    Rejects multi-statements, data modification, DDL, and dangerous syntax.
    """

    @classmethod
    def validate(cls, raw_sql: str) -> str:
        """
        Validates raw SQL and returns clean formatted SQL if valid.
        Raises SQLValidationError if invalid.
        """
        if not raw_sql or not raw_sql.strip():
            raise SQLValidationError("SQL query cannot be empty.")

        # Strip comments and extra spaces
        cleaned = raw_sql.strip()
        parsed = sqlparse.parse(cleaned)

        # Filter out empty or whitespace-only statements
        statements = [stmt for stmt in parsed if str(stmt).strip().rstrip(";").strip()]

        if len(statements) == 0:
            raise SQLValidationError("No executable SQL statements found.")

        if len(statements) > 1:
            raise SQLValidationError(
                f"Execution of multiple SQL statements is rejected for security. Found {len(statements)} statements."
            )

        stmt = statements[0]
        stmt_type = stmt.get_type()

        # Check statement type
        # In sqlparse, CTE statements start with WITH and their get_type() might be 'SELECT' or 'UNKNOWN'
        raw_upper = cleaned.upper()
        first_token = cls._get_first_meaningful_token(stmt)
        first_word = first_token.value.upper() if first_token else ""

        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            raise SQLValidationError(
                f"Only read-only SELECT queries are permitted. Statement begins with: '{first_word}'"
            )

        # Deep inspect tokens for any forbidden keywords (even inside subqueries or comments)
        cls._check_tokens_for_forbidden_keywords(stmt)

        # Format and return the safe SQL
        formatted = sqlparse.format(
            cleaned.rstrip(";"),
            reindent=True,
            keyword_case="upper",
            identifier_case="lower",
            strip_comments=True
        )

        return formatted

    @classmethod
    def _get_first_meaningful_token(cls, token_list: TokenList) -> Optional[Token]:
        for token in token_list.tokens:
            if not token.is_whitespace and not token.ttype in sqlparse.tokens.Comment:
                return token
        return None

    @classmethod
    def _check_tokens_for_forbidden_keywords(cls, token_list: TokenList):
        for token in token_list.tokens:
            if token.is_group:
                cls._check_tokens_for_forbidden_keywords(token)
            else:
                val = token.value.upper().strip()
                if val in FORBIDDEN_KEYWORDS:
                    raise SQLValidationError(
                        f"Prohibited SQL keyword detected: '{val}'. Only read-only operations are permitted."
                    )
                # Check for INTO ... clause (e.g. SELECT ... INTO table)
                if val == "INTO" and token.ttype in (Keyword, DML):
                    raise SQLValidationError("SELECT INTO is prohibited as it modifies the database.")
