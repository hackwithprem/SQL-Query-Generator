from backend.database.connection import get_connection


def get_schema():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    schema = {}

    for table_name, column_name, data_type in rows:
        if table_name not in schema:
            schema[table_name] = []

        schema[table_name].append({
            "column": column_name,
            "type": data_type
        })

    return schema