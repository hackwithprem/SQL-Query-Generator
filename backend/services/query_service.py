from backend.database.connection import get_connection
from backend.validation.sql_validator import validate_sql


def execute_query(sql):
    is_valid, message = validate_sql(sql)

    if not is_valid:
        return {
            "success": False,
            "error": message
        }

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]

        return {
            "success": True,
            "columns": columns,
            "rows": rows
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        cursor.close()
        conn.close()