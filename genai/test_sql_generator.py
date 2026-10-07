from sql_generator import SQLGenerator


schema = """
students(
    id,
    name,
    department,
    marks
)
"""

question = input("Enter your question: ")

generator = SQLGenerator()

sql = generator.generate_sql(schema, question)

print("\nGenerated SQL:")
print(sql)