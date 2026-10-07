from sql_corrector import SQLCorrector


schema = """
students(
    id,
    name,
    department,
    marks
)
"""

sql = "SELECT * FROM students WHERE mark > 70;"

error_message = "column 'mark' does not exist"

corrector = SQLCorrector()

corrected_sql = corrector.correct_sql(
    schema,
    sql,
    error_message
)

print("\nCorrected SQL:")
print(corrected_sql)