import os
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from app.core.config import settings

def strip_markdown_code_fences(text: str) -> str:
    """Removes ```sql and ``` markdown markers if the LLM wraps the SQL."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line if ``` or ```sql
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Remove last line if ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned

class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def generate_sql(
        self, 
        question: str, 
        schema_context: str, 
        dialect: str = "sqlite",
        retrieved_examples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Translates a natural language question into a safe SQL query."""
        pass

    @abstractmethod
    def explain_sql(self, sql: str, schema_context: str, question: Optional[str] = None) -> Dict[str, Any]:
        """Provides a natural language explanation of the SQL query."""
        pass

    @abstractmethod
    def correct_sql(self, question: str, failed_sql: str, error_msg: str, schema_context: str) -> Tuple[str, str]:
        """Corrects a failed SQL query, returning (corrected_sql, explanation_of_fix)."""
        pass

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
        if api_key and api_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._client = Groq(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")

    @property
    def provider_name(self) -> str:
        return f"Groq ({self.model_name})"

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def generate_sql(
        self, 
        question: str, 
        schema_context: str, 
        dialect: str = "sqlite",
        retrieved_examples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self.is_configured:
            raise RuntimeError("Groq API key is not configured.")

        has_schema = schema_context.strip() and schema_context.strip() != "No schema available."

        if has_schema:
            schema_rules = f"""3. Use ONLY the tables, columns, and relationships defined in the database schema below. Do NOT invent columns or tables.
4. If the question can be answered using the schema, return ONLY the raw SQL query. Do NOT include markdown code blocks, do not include explanations, and do not include extra commentary.

DATABASE SCHEMA:
{schema_context}"""
        else:
            schema_rules = f"""3. No database schema is available. Generate the most reasonable SQL query using conventional, widely-accepted table and column names that match the user's question. Use standard naming conventions (e.g., products, product_name, price, customers, orders).
4. Return ONLY the raw SQL query. Do NOT include markdown code blocks, do not include explanations, and do not include extra commentary. Do NOT return SCHEMA_ERROR.

DATABASE SCHEMA:
(No schema provided — use best-practice naming assumptions)"""

        examples_section = ""
        if retrieved_examples:
            from app.services.rag.rag_service import RAGService
            formatted = RAGService.format_examples_for_prompt(retrieved_examples)
            if formatted:
                examples_section = f"\n\n{formatted}"

        system_prompt = f"""You are an expert SQL engineer.
Your task is to translate natural language questions into accurate, high-performance, and safe SQL queries for {dialect.upper()}.

CRITICAL SECURITY AND ACCURACY RULES:
1. ONLY produce read-only SELECT queries.
2. NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, or multiple statements.
{schema_rules}{examples_section}
"""

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Question: {question}\nGenerate SQL:"}
            ],
            temperature=0.1,
            max_tokens=600,
        )

        raw_output = response.choices[0].message.content or ""
        return strip_markdown_code_fences(raw_output)

    def explain_sql(self, sql: str, schema_context: str, question: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("Groq API key is not configured.")

        prompt = f"""Explain this SQL query in clear, simple English for a student or business analyst.
SQL Query:
{sql}

Database Schema Context:
{schema_context}

Original Question (if any):
{question or 'N/A'}

Format your response in two parts:
1. A concise overview paragraph (2-3 sentences max) explaining what this query accomplishes.
2. Bullet points breaking down:
   - The tables being queried
   - The conditions/filters applied
   - Any aggregations, groupings, or ordering applied
"""
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a database teacher who explains SQL clearly and simply."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600,
        )
        explanation = response.choices[0].message.content or ""
        return {"explanation": explanation}

    def correct_sql(self, question: str, failed_sql: str, error_msg: str, schema_context: str) -> Tuple[str, str]:
        if not self.is_configured:
            raise RuntimeError("Groq API key is not configured.")

        prompt = f"""The following SQL query failed with a database error. Please analyze the error, fix the SQL query using the provided schema, and explain the fix.

Original User Question:
{question}

Failed SQL:
{failed_sql}

Database Error Message:
{error_msg}

Database Schema Context:
{schema_context}

Instructions:
1. Provide the corrected SQL query inside a ```sql code block.
2. Below the code block, provide a 1-2 sentence explanation of what went wrong and how you fixed it.
"""
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert SQL debugger. Correct SQL errors safely and accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800,
        )
        content = response.choices[0].message.content or ""
        
        # Extract corrected SQL
        match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            corrected_sql = match.group(1).strip()
            explanation_part = content[match.end():].strip()
        else:
            lines = content.split("\n")
            corrected_sql = lines[0].strip()
            explanation_part = "\n".join(lines[1:]).strip()

        return corrected_sql, explanation_part or "Corrected SQL syntax and aligned with database schema."


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
        if api_key and api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self.model_name})"

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def generate_sql(
        self, 
        question: str, 
        schema_context: str, 
        dialect: str = "sqlite",
        retrieved_examples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self.is_configured:
            raise RuntimeError("Gemini API key is not configured.")

        has_schema = schema_context.strip() and schema_context.strip() != "No schema available."

        if has_schema:
            schema_instruction = f"""Use ONLY the tables and columns defined in the schema below:
{schema_context}

If the question can be answered using the schema, return ONLY the raw SQL query with no extra text or markdown fences."""
        else:
            schema_instruction = f"""No database schema is provided. Generate the most reasonable SQL query using conventional, widely-accepted table and column names that match the user's question. Use standard naming conventions (e.g., products, product_name, price, customers, orders).
Return ONLY the raw SQL query with no extra text or markdown fences. Do NOT return SCHEMA_ERROR."""

        examples_instruction = ""
        if retrieved_examples:
            from app.services.rag.rag_service import RAGService
            formatted = RAGService.format_examples_for_prompt(retrieved_examples)
            if formatted:
                examples_instruction = f"\n4. {formatted}\n"

        prompt = f"""You are an expert SQL engineer.
Translate this natural language question into an accurate, safe SQL query for {dialect.upper()}.

CRITICAL RULES:
1. ONLY produce read-only SELECT queries.
2. NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, or multiple statements.
3. {schema_instruction}
{examples_instruction}
Question: {question}
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        raw_output = response.text or ""
        return strip_markdown_code_fences(raw_output)

    def explain_sql(self, sql: str, schema_context: str, question: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("Gemini API key is not configured.")

        prompt = f"""Explain this SQL query in clear, simple English:
SQL: {sql}
Schema: {schema_context}
Question: {question or 'N/A'}
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return {"explanation": response.text or ""}

    def correct_sql(self, question: str, failed_sql: str, error_msg: str, schema_context: str) -> Tuple[str, str]:
        if not self.is_configured:
            raise RuntimeError("Gemini API key is not configured.")

        prompt = f"""Fix this failed SQL query.
Original Question: {question}
Failed SQL: {failed_sql}
Error: {error_msg}
Schema: {schema_context}

Return the corrected SQL inside a ```sql code block followed by a brief explanation.
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        content = response.text or ""
        match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            corrected_sql = match.group(1).strip()
            explanation_part = content[match.end():].strip()
        else:
            corrected_sql = content.strip()
            explanation_part = "Fixed query error based on database schema."
        return corrected_sql, explanation_part


class MockOfflineProvider(BaseLLMProvider):
    """
    Intelligent offline provider that enables full system testing and demonstration
    even when no external API keys are configured or internet is unavailable.
    """

    @property
    def provider_name(self) -> str:
        return "Local Pattern Engine (Offline Demo Fallback)"

    @property
    def is_configured(self) -> bool:
        return True

    def generate_sql(
        self, 
        question: str, 
        schema_context: str, 
        dialect: str = "sqlite",
        retrieved_examples: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        q = question.lower().strip()

        # Handle uploaded dataset or custom table schema dynamically
        if "Available Table:" in schema_context:
            match = re.search(r"Available Table:\s*([a-zA-Z0-9_]+)", schema_context)
            if match:
                table_name = match.group(1)
                col_matches = re.findall(r"-\s*([a-zA-Z0-9_]+):", schema_context)
                cols_str = ", ".join(col_matches) if col_matches else "*"

                num_match = re.search(r"(?:more than|greater than|>|above|earning more than)\s*(\d+)", q)
                val_col = next((c for c in col_matches if any(k in c.lower() for k in ["salary", "amount", "revenue", "price", "score", "marks"])), None)

                if num_match and val_col:
                    threshold = num_match.group(1)
                    return f"SELECT {cols_str} FROM {table_name} WHERE {val_col} > {threshold} ORDER BY {val_col} DESC LIMIT 500;"
                elif "count" in q:
                    return f"SELECT COUNT(*) AS total_records FROM {table_name};"
                elif "top" in q:
                    order_col = val_col or (col_matches[0] if col_matches else "1")
                    return f"SELECT {cols_str} FROM {table_name} ORDER BY {order_col} DESC LIMIT 5;"
                elif "average" in q or "avg" in q:
                    target_num_col = val_col or (col_matches[0] if col_matches else "*")
                    return f"SELECT ROUND(AVG({target_num_col}), 2) AS average_value FROM {table_name};"
                else:
                    return f"SELECT {cols_str} FROM {table_name} LIMIT 500;"

        # Comprehensive rule-based and intent matching for academic sample dataset
        if "more than 80" in q or "> 80" in q or "over 80" in q or "scored more than 80" in q:
            return """SELECT DISTINCT s.id, s.first_name, s.last_name, c.title AS course, m.score, m.grade
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id
JOIN marks m ON e.id = m.enrollment_id
WHERE m.score > 80
ORDER BY m.score DESC;"""

        if "top five" in q or "top 5" in q:
            return """SELECT id, first_name, last_name, gpa, enrollment_year
FROM students
ORDER BY gpa DESC
LIMIT 5;"""

        if "all student" in q or "show students" in q or "list students" in q or "get all students" in q:
            return """SELECT s.id, s.first_name, s.last_name, s.email, s.age, s.gender, s.gpa, d.name AS department
FROM students s
LEFT JOIN departments d ON s.department_id = d.id
ORDER BY s.id ASC;"""

        if "all course" in q or "list courses" in q or "show courses" in q:
            return """SELECT c.id, c.course_code, c.title, c.credits, c.instructor, d.name AS department
FROM courses c
LEFT JOIN departments d ON c.department_id = d.id;"""

        if "all department" in q or "list departments" in q:
            return "SELECT id, name, code, budget FROM departments ORDER BY name ASC;"

        if "average mark" in q or "avg mark" in q or "average score" in q:
            return """SELECT c.title AS course_name, ROUND(AVG(m.score), 2) AS average_score, COUNT(m.id) AS total_exams
FROM courses c
JOIN enrollments e ON c.id = e.course_id
JOIN marks m ON e.id = m.enrollment_id
GROUP BY c.id, c.title
ORDER BY average_score DESC;"""

        if "highest mark" in q or "max mark" in q or "top score" in q:
            return """SELECT s.first_name, s.last_name, c.title AS course, m.score, m.grade
FROM marks m
JOIN enrollments e ON m.enrollment_id = e.id
JOIN students s ON e.student_id = s.id
JOIN courses c ON e.course_id = c.id
ORDER BY m.score DESC
LIMIT 1;"""

        if "count" in q and "student" in q and ("course" in q or "by course" in q or "per course" in q):
            return """SELECT c.course_code, c.title, COUNT(e.student_id) AS student_count
FROM courses c
LEFT JOIN enrollments e ON c.id = e.course_id
GROUP BY c.id, c.course_code, c.title
ORDER BY student_count DESC;"""

        if "count" in q and "student" in q:
            return "SELECT COUNT(*) AS total_students FROM students;"

        if "enrolled in more than one" in q or "more than 1 course" in q:
            return """SELECT s.id, s.first_name, s.last_name, COUNT(e.course_id) AS enrolled_courses_count
FROM students s
JOIN enrollments e ON s.id = e.student_id
GROUP BY s.id, s.first_name, s.last_name
HAVING COUNT(e.course_id) > 1
ORDER BY enrolled_courses_count DESC;"""

        if "no enrolled students" in q or "zero students" in q or "without students" in q:
            return """SELECT c.id, c.course_code, c.title, c.instructor
FROM courses c
LEFT JOIN enrollments e ON c.id = e.course_id
WHERE e.id IS NULL;"""

        if "computer science" in q or "cs students" in q:
            return """SELECT s.id, s.first_name, s.last_name, s.email, s.gpa
FROM students s
JOIN departments d ON s.department_id = d.id
WHERE d.code = 'CS'
ORDER BY s.gpa DESC;"""

        if "gpa" in q and ("greater" in q or ">" in q or "above" in q or "higher" in q):
            return "SELECT id, first_name, last_name, email, gpa FROM students WHERE gpa >= 3.5 ORDER BY gpa DESC;"

        # Check if the question asks for entities not present in the University Sample DB schema
        sample_tables = ["student", "course", "department", "enrollment", "mark"]
        if not any(t in q for t in sample_tables):
            # No schema context — generate reasonable SQL using conventional naming conventions
            # Detect the primary entity from common patterns
            entity_map = {
                "product": ("products", ["product_id", "product_name", "price", "category", "stock_quantity"]),
                "item": ("items", ["item_id", "item_name", "price", "quantity"]),
                "order": ("orders", ["order_id", "customer_id", "order_date", "total_amount", "status"]),
                "customer": ("customers", ["customer_id", "first_name", "last_name", "email", "phone"]),
                "employee": ("employees", ["employee_id", "first_name", "last_name", "department", "salary"]),
                "sale": ("sales", ["sale_id", "product_id", "quantity", "sale_date", "revenue"]),
                "inventory": ("inventory", ["item_id", "item_name", "quantity", "warehouse_location"]),
                "book": ("books", ["book_id", "title", "author", "genre", "price"]),
                "user": ("users", ["user_id", "username", "email", "created_at", "role"]),
            }

            matched_entity = None
            for kw, (table, cols) in entity_map.items():
                if kw in q:
                    matched_entity = (table, cols)
                    break

            if matched_entity:
                table, cols = matched_entity

                # Detect query intent
                num_match = re.search(r"(?:more than|greater than|>|above|over)\s*(\d+)", q)
                val_col = next((c for c in cols if any(k in c.lower() for k in ["price", "salary", "amount", "revenue", "quantity"])), None)

                col_select = ", ".join(cols)

                if num_match and val_col:
                    threshold = num_match.group(1)
                    return f"SELECT {col_select} FROM {table} WHERE {val_col} > {threshold} ORDER BY {val_col} DESC;"
                elif any(w in q for w in ["count", "how many", "total number"]):
                    return f"SELECT COUNT(*) AS total_{table} FROM {table};"
                elif any(w in q for w in ["average", "avg"]) and val_col:
                    return f"SELECT ROUND(AVG({val_col}), 2) AS average_{val_col} FROM {table};"
                elif any(w in q for w in ["top", "highest", "most expensive"]) and val_col:
                    return f"SELECT {col_select} FROM {table} ORDER BY {val_col} DESC LIMIT 10;"
                elif any(w in q for w in ["cheapest", "lowest", "minimum"]) and val_col:
                    return f"SELECT {col_select} FROM {table} ORDER BY {val_col} ASC LIMIT 10;"
                else:
                    # Generic: list all with assumed relevant columns
                    # Prefer name + price or relevant value columns for display
                    display_cols = [c for c in cols if any(k in c.lower() for k in ["name", "title", "price", "salary", "date", "email", "status"])]
                    primary_key = cols[0] if cols else f"{table}_id"
                    select_cols = ", ".join([primary_key] + display_cols) if display_cols else col_select
                    return f"SELECT {select_cols} FROM {table};"

            # Generic free-form question with no recognized entity — generate a safe placeholder query
            return "SELECT * FROM your_table_name LIMIT 50;"

        # Default intelligent fallback for any other general query
        return """SELECT s.id, s.first_name, s.last_name, s.email, s.gpa, d.name AS department
FROM students s
LEFT JOIN departments d ON s.department_id = d.id
LIMIT 20;"""

    def explain_sql(self, sql: str, schema_context: str, question: Optional[str] = None) -> Dict[str, Any]:
        sql_upper = sql.upper()
        tables_mentioned = [t for t in ["students", "courses", "enrollments", "marks", "departments"] if t in sql.lower()]
        has_join = "JOIN" in sql_upper
        has_where = "WHERE" in sql_upper
        has_group = "GROUP BY" in sql_upper
        has_order = "ORDER BY" in sql_upper
        has_limit = "LIMIT" in sql_upper

        bullets = []
        if tables_mentioned:
            bullets.append(f"• **Tables Accessed**: Reads information from `{', '.join(tables_mentioned)}`.")
        if has_join:
            bullets.append("• **Joins**: Connects records across tables using relational foreign keys (e.g. matching student IDs and course IDs).")
        if has_where:
            bullets.append("• **Filtering**: Applies specific criteria in the WHERE clause to isolate relevant records.")
        if has_group:
            bullets.append("• **Aggregation & Grouping**: Groups data to calculate summary statistics (e.g., COUNT, AVG).")
        if has_order:
            bullets.append("• **Sorting**: Orders results in ascending or descending sequence for clear presentation.")
        if has_limit:
            bullets.append("• **Row Limit**: Restricts output volume for optimal responsiveness.")

        overview = (
            f"This SQL query queries the database to retrieve data from {', '.join(tables_mentioned) if tables_mentioned else 'the tables'}."
            f" It applies { 'relational joins and filters' if has_join else 'structured selection' } to produce the targeted answer."
        )

        return {
            "explanation": f"{overview}\n\n" + "\n".join(bullets)
        }

    def correct_sql(self, question: str, failed_sql: str, error_msg: str, schema_context: str) -> Tuple[str, str]:
        # Handle common issues: syntax typo, wrong column name, missing table
        fixed = failed_sql
        explanation = "Detected and corrected query issue."

        # If typo in table/column
        if "no such column" in error_msg.lower():
            col_match = re.search(r"no such column:\s*([a-zA-Z0-9_\.]+)", error_msg, re.IGNORECASE)
            bad_col = col_match.group(1) if col_match else "unknown"
            fixed = re.sub(r"\bname\b", "first_name, last_name", fixed, flags=re.IGNORECASE)
            fixed = re.sub(r"\bscore_marks\b", "score", fixed, flags=re.IGNORECASE)
            explanation = f"Replaced invalid column reference `{bad_col}` with the correct columns present in the schema."
        elif "syntax error" in error_msg.lower():
            fixed = fixed.rstrip(";") + ";"
            explanation = "Corrected SQL syntax error and ensured valid clause ordering."
        else:
            # Fallback to standard safe query
            fixed = "SELECT s.id, s.first_name, s.last_name, s.gpa FROM students s ORDER BY s.gpa DESC LIMIT 10;"
            explanation = "Reconstructed query to match valid schema tables and columns."

        return fixed, explanation

def get_llm_provider() -> BaseLLMProvider:
    provider_choice = settings.LLM_PROVIDER.lower().strip()

    if provider_choice == "groq" and settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
        provider = GroqProvider(api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL)
        if provider.is_configured:
            return provider

    if provider_choice == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        provider = GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        if provider.is_configured:
            return provider

    # Default fallback to mock offline provider
    return MockOfflineProvider()
