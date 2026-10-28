from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    budget = Column(Float, default=0.0)

    students = relationship("Student", back_populates="department")
    courses = relationship("Course", back_populates="department")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10))
    enrollment_year = Column(Integer, nullable=False)
    gpa = Column(Float, default=0.0)
    department_id = Column(Integer, ForeignKey("departments.id"))

    department = relationship("Department", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_code = Column(String(20), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    instructor = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))

    department = relationship("Department", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester = Column(String(20), nullable=False)
    enrollment_date = Column(Date, nullable=False)
    status = Column(String(20), default="Enrolled") # Enrolled, Completed, Dropped

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    marks = relationship("Mark", back_populates="enrollment")

class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    exam_type = Column(String(50), nullable=False) # Midterm, Final, Assignment, Project
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    grade = Column(String(5))

    enrollment = relationship("Enrollment", back_populates="marks")

class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    natural_query = Column(String, nullable=False)
    generated_sql = Column(String, nullable=False)
    executed = Column(Integer, default=0) # 0 = False, 1 = True
    status = Column(String(20), default="generated") # generated, executed, failed
    execution_time_ms = Column(Float, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
