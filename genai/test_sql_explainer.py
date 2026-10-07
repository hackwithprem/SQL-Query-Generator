from sql_explainer import SQLExplainer


schema = """
students(
    id,
    name,
    department,
    marks
)
"""

sql = """
SELECT * FROM students
WHERE department = 'Computer Science'
AND marks > 70
ORDER BY marks DESC
LIMIT 5;
"""

explainer = SQLExplainer()

explanation = explainer.explain_sql(schema, sql)

print("\nSQL Explanation:")
print(explanation)