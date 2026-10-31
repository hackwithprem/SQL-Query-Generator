import datetime
from sqlalchemy.orm import Session
from app.database.connection import engine, Base, SessionLocal
from app.database.models import User, Department, Student, Course, Enrollment, Mark, QueryHistory, UploadedDataset, DatabaseConnectionModel
from app.core.security import hash_password

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # Create all tables if not exist
        Base.metadata.create_all(bind=engine)

        # Migration: Ensure user_id column exists on query_history for existing SQLite database
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(query_history)")).fetchall()
                col_names = [r[1] for r in res]
                if "user_id" not in col_names:
                    conn.execute(text("ALTER TABLE query_history ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                    conn.commit()

                # Migration for users.supabase_id
                res_u = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                u_cols = [r[1] for r in res_u]
                if "supabase_id" not in u_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN supabase_id VARCHAR(64)"))
                    conn.commit()

                # Migration for uploaded_datasets.storage_path
                res_d = conn.execute(text("PRAGMA table_info(uploaded_datasets)")).fetchall()
                d_cols = [r[1] for r in res_d]
                if "storage_path" not in d_cols:
                    conn.execute(text("ALTER TABLE uploaded_datasets ADD COLUMN storage_path VARCHAR(255)"))
                    conn.commit()
        except Exception as e:
            print(f"Migration notice: {e}")

        # Seed default demo user if not present
        if db.query(User).filter(User.email == "demo@example.com").first() is None:
            demo_user = User(
                full_name="Alex Morgan",
                email="demo@example.com",
                hashed_password=hash_password("DemoUser123!"),
            )
            db.add(demo_user)
            db.commit()

        # Check if academic data is already seeded
        if db.query(Department).count() > 0:
            return

        print("Seeding database with sample academic data...")

        # 1. Departments
        departments = [
            Department(id=1, name="Computer Science", code="CS", budget=850000.0),
            Department(id=2, name="Mathematics", code="MATH", budget=420000.0),
            Department(id=3, name="Electrical Engineering", code="EE", budget=750000.0),
            Department(id=4, name="Biology", code="BIO", budget=510000.0),
            Department(id=5, name="Business Administration", code="BUS", budget=630000.0),
        ]
        db.add_all(departments)
        db.flush()

        # 2. Courses
        courses = [
            Course(id=1, course_code="CS101", title="Intro to Computer Science", credits=4, instructor="Dr. Alan Turing", department_id=1),
            Course(id=2, course_code="CS201", title="Data Structures & Algorithms", credits=4, instructor="Dr. Grace Hopper", department_id=1),
            Course(id=3, course_code="CS301", title="Database Systems", credits=3, instructor="Dr. Edgar Codd", department_id=1),
            Course(id=4, course_code="MATH101", title="Calculus I", credits=4, instructor="Dr. Isaac Newton", department_id=2),
            Course(id=5, course_code="MATH201", title="Linear Algebra", credits=3, instructor="Dr. Carl Gauss", department_id=2),
            Course(id=6, course_code="EE101", title="Circuit Analysis", credits=4, instructor="Dr. Nikola Tesla", department_id=3),
            Course(id=7, course_code="BIO101", title="General Biology", credits=3, instructor="Dr. Charles Darwin", department_id=4),
            Course(id=8, course_code="BUS101", title="Principles of Management", credits=3, instructor="Dr. Peter Drucker", department_id=5),
            Course(id=9, course_code="CS401", title="Advanced Artificial Intelligence", credits=4, instructor="Dr. Geoffrey Hinton", department_id=1),
        ]
        db.add_all(courses)
        db.flush()

        # 3. Students
        students = [
            Student(id=1, first_name="Alice", last_name="Johnson", email="alice.johnson@university.edu", age=20, gender="Female", enrollment_year=2023, gpa=3.85, department_id=1),
            Student(id=2, first_name="Bob", last_name="Smith", email="bob.smith@university.edu", age=22, gender="Male", enrollment_year=2022, gpa=3.20, department_id=1),
            Student(id=3, first_name="Charlie", last_name="Brown", email="charlie.brown@university.edu", age=19, gender="Male", enrollment_year=2024, gpa=3.65, department_id=2),
            Student(id=4, first_name="Diana", last_name="Prince", email="diana.prince@university.edu", age=21, gender="Female", enrollment_year=2022, gpa=3.95, department_id=3),
            Student(id=5, first_name="Ethan", last_name="Hunt", email="ethan.hunt@university.edu", age=23, gender="Male", enrollment_year=2021, gpa=2.85, department_id=5),
            Student(id=6, first_name="Fiona", last_name="Gallagher", email="fiona.gallagher@university.edu", age=20, gender="Female", enrollment_year=2023, gpa=3.40, department_id=4),
            Student(id=7, first_name="George", last_name="Clark", email="george.clark@university.edu", age=22, gender="Male", enrollment_year=2022, gpa=3.10, department_id=1),
            Student(id=8, first_name="Hannah", last_name="Abbott", email="hannah.abbott@university.edu", age=21, gender="Female", enrollment_year=2023, gpa=3.75, department_id=2),
            Student(id=9, first_name="Ian", last_name="Malcolm", email="ian.malcolm@university.edu", age=24, gender="Male", enrollment_year=2021, gpa=2.90, department_id=4),
            Student(id=10, first_name="Julia", last_name="Roberts", email="julia.roberts@university.edu", age=19, gender="Female", enrollment_year=2024, gpa=3.55, department_id=5),
            Student(id=11, first_name="Kevin", last_name="Bacon", email="kevin.bacon@university.edu", age=22, gender="Male", enrollment_year=2022, gpa=3.30, department_id=3),
            Student(id=12, first_name="Laura", last_name="Croft", email="laura.croft@university.edu", age=21, gender="Female", enrollment_year=2023, gpa=3.90, department_id=1),
        ]
        db.add_all(students)
        db.flush()

        # 4. Enrollments
        enrollment_specs = [
            # Alice (CS)
            (1, 1, 1, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            (2, 1, 2, "Spring 2024", datetime.date(2024, 1, 15), "Completed"),
            (3, 1, 3, "Fall 2024", datetime.date(2024, 9, 1), "Enrolled"),
            # Bob (CS)
            (4, 2, 1, "Fall 2022", datetime.date(2022, 9, 1), "Completed"),
            (5, 2, 3, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            # Charlie (MATH)
            (6, 3, 4, "Spring 2024", datetime.date(2024, 1, 15), "Completed"),
            (7, 3, 5, "Fall 2024", datetime.date(2024, 9, 1), "Enrolled"),
            (8, 3, 1, "Fall 2024", datetime.date(2024, 9, 1), "Enrolled"),
            # Diana (EE)
            (9, 4, 6, "Fall 2022", datetime.date(2022, 9, 1), "Completed"),
            (10, 4, 4, "Spring 2023", datetime.date(2023, 1, 15), "Completed"),
            (11, 4, 1, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            # Ethan (BUS)
            (12, 5, 8, "Fall 2021", datetime.date(2021, 9, 1), "Completed"),
            (13, 5, 3, "Spring 2022", datetime.date(2022, 1, 15), "Dropped"),
            # Fiona (BIO)
            (14, 6, 7, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            # George (CS)
            (15, 7, 1, "Fall 2022", datetime.date(2022, 9, 1), "Completed"),
            (16, 7, 2, "Spring 2023", datetime.date(2023, 1, 15), "Completed"),
            (17, 7, 3, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            # Hannah (MATH)
            (18, 8, 4, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            (19, 8, 5, "Spring 2024", datetime.date(2024, 1, 15), "Completed"),
            # Ian (BIO)
            (20, 9, 7, "Fall 2021", datetime.date(2021, 9, 1), "Completed"),
            # Julia (BUS)
            (21, 10, 8, "Spring 2024", datetime.date(2024, 1, 15), "Completed"),
            # Laura (CS)
            (22, 12, 1, "Fall 2023", datetime.date(2023, 9, 1), "Completed"),
            (23, 12, 2, "Spring 2024", datetime.date(2024, 1, 15), "Completed"),
            (24, 12, 3, "Fall 2024", datetime.date(2024, 9, 1), "Enrolled"),
            (25, 12, 5, "Fall 2024", datetime.date(2024, 9, 1), "Enrolled"),
        ]

        enrollments = [
            Enrollment(id=eid, student_id=sid, course_id=cid, semester=sem, enrollment_date=edate, status=st)
            for eid, sid, cid, sem, edate, st in enrollment_specs
        ]
        db.add_all(enrollments)
        db.flush()

        # 5. Marks
        # (enrollment_id, exam_type, score, max_score, grade)
        marks_data = [
            # Alice CS101
            (1, "Midterm", 92.0, 100.0, "A"),
            (1, "Final", 95.0, 100.0, "A"),
            # Alice CS201
            (2, "Midterm", 88.0, 100.0, "B+"),
            (2, "Final", 91.5, 100.0, "A-"),
            # Bob CS101
            (4, "Midterm", 74.0, 100.0, "C+"),
            (4, "Final", 78.5, 100.0, "B-"),
            # Bob CS301
            (5, "Midterm", 82.0, 100.0, "B"),
            (5, "Final", 80.0, 100.0, "B"),
            # Charlie MATH101
            (6, "Midterm", 89.0, 100.0, "B+"),
            (6, "Final", 93.0, 100.0, "A"),
            # Diana EE101
            (9, "Midterm", 96.0, 100.0, "A+"),
            (9, "Final", 98.0, 100.0, "A+"),
            # Diana MATH101
            (10, "Midterm", 94.0, 100.0, "A"),
            (10, "Final", 95.5, 100.0, "A"),
            # Diana CS101
            (11, "Midterm", 91.0, 100.0, "A-"),
            (11, "Final", 94.0, 100.0, "A"),
            # Ethan BUS101
            (12, "Midterm", 68.0, 100.0, "C"),
            (12, "Final", 72.0, 100.0, "C+"),
            # Fiona BIO101
            (14, "Midterm", 84.0, 100.0, "B"),
            (14, "Final", 86.5, 100.0, "B+"),
            # George CS101
            (15, "Midterm", 77.0, 100.0, "B-"),
            (15, "Final", 81.0, 100.0, "B"),
            # Hannah MATH101
            (18, "Midterm", 88.0, 100.0, "B+"),
            (18, "Final", 90.0, 100.0, "A-"),
            # Ian BIO101
            (20, "Midterm", 65.0, 100.0, "D+"),
            (20, "Final", 70.0, 100.0, "C-"),
            # Julia BUS101
            (21, "Midterm", 85.0, 100.0, "B"),
            (21, "Final", 89.0, 100.0, "B+"),
            # Laura CS101
            (22, "Midterm", 95.0, 100.0, "A"),
            (22, "Final", 97.0, 100.0, "A+"),
            # Laura CS201
            (23, "Midterm", 92.5, 100.0, "A"),
            (23, "Final", 94.0, 100.0, "A"),
        ]

        marks = [
            Mark(enrollment_id=eid, exam_type=etype, score=sc, max_score=msc, grade=gr)
            for eid, etype, sc, msc, gr in marks_data
        ]
        db.add_all(marks)
        db.commit()
        print("Database successfully seeded!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_database()
