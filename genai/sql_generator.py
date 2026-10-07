import os
from google import genai


class SQLGenerator:

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.6-flash"

    def generate_sql(self, schema, question):

        prompt = f"""
You are an expert SQL query generator.

Convert the user's natural language question into a valid SQL query.

Database schema:
{schema}

Rules:
1. Use only tables and columns present in the schema.
2. Do not invent, rename, or substitute columns.
3. If the user's question refers to a column that does not exist in the schema, return exactly: INVALID_QUERY
4. Generate valid SQL only when the requested information can be obtained from the schema.
5. Return only the SQL query or INVALID_QUERY.
6. Do not include explanations or markdown.

User question:
{question}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            sql = response.text.strip()

        except Exception as e:
            return f"API_ERROR: {e}"

        if sql.startswith("```sql"):
            sql = sql[len("```sql"):]

        if sql.startswith("```"):
            sql = sql[len("```"):]

        if sql.endswith("```"):
            sql = sql[:-len("```")]

        return sql.strip()