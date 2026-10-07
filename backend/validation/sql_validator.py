import re


def validate_sql(sql):
    sql = sql.strip()

    if not sql:
        return False, "SQL query is empty."

    # Allow only SELECT queries
    if not re.match(r"^SELECT\b", sql, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."

    # Block dangerous SQL operations
    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE"
    ]

    for command in forbidden:
        if re.search(rf"\b{command}\b", sql, re.IGNORECASE):
            return False, f"{command} operation is not allowed."

    return True, "SQL query is valid."