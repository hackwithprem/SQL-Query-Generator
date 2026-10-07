class PromptBuilder:

    def build_sql_prompt(self, schema, question):

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

        return prompt

    def build_correction_prompt(self, schema, sql, error_message):

        prompt = f"""
You are an expert SQL debugging assistant.

Correct the SQL query based on the database schema and error message.

Database schema:
{schema}

SQL query:
{sql}

Database error:
{error_message}

Rules:
1. Use only tables and columns present in the schema.
2. Fix the SQL query according to the error.
3. Return only the corrected SQL query.
4. Do not include explanations.
5. Do not use markdown code blocks.
"""

        return prompt

    def build_explanation_prompt(self, schema, sql):

        prompt = f"""
You are an expert SQL teacher.

Explain the following SQL query in simple language.

Database schema:
{schema}

SQL query:
{sql}

Rules:
1. Explain what the query does.
2. Explain the important parts of the query.
3. Keep the explanation simple and easy to understand.
4. Do not generate a new SQL query.
"""

        return prompt