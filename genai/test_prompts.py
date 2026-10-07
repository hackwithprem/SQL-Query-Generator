from sql_generator import SQLGenerator


schema = """
students(
    id,
    name,
    department,
    marks
)
"""

test_questions = [
    "Show all students.",
    "Show students from the Computer Science department.",
    "Show students who scored more than 80 marks.",
    "Show the top 5 students by marks.",
    "Show Computer Science students who scored more than 70 marks.",
    "Show students whose GPA is above 8."
]


generator = SQLGenerator()

for i, question in enumerate(test_questions, start=1):

    print(f"\nTest {i}")
    print(f"Question: {question}")

    try:
        sql = generator.generate_sql(schema, question)
        print(f"SQL: {sql}")

    except Exception as e:
        print(f"ERROR: {e}")