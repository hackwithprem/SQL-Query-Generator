from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supabase_id = Column(String(64), unique=True, nullable=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    history = relationship("QueryHistory", back_populates="user", cascade="all, delete-orphan")
    datasets = relationship("UploadedDataset", back_populates="user", cascade="all, delete-orphan")
    connections = relationship("DatabaseConnectionModel", back_populates="user", cascade="all, delete-orphan")

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    natural_query = Column(String, nullable=False)
    generated_sql = Column(String, nullable=False)
    executed = Column(Integer, default=0) # 0 = False, 1 = True
    status = Column(String(20), default="generated") # generated, executed, failed
    execution_time_ms = Column(Float, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="history")

class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"

    id = Column(String(36), primary_key=True, index=True) # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(20), nullable=False) # 'csv' or 'excel'
    sheet_name = Column(String(100), nullable=True)
    table_name = Column(String(64), nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    columns_json = Column(Text, nullable=False) # JSON array of {name, display_name, type}
    sqlite_db_path = Column(String(255), nullable=False)
    storage_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="datasets")

class DatabaseConnectionModel(Base):
    __tablename__ = "database_connections"

    id = Column(String(36), primary_key=True, index=True) # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False) # 'oracle', 'postgresql', 'mysql'
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    encrypted_password = Column(String(500), nullable=False)
    ssl_enabled = Column(Boolean, default=False)
    extra_params = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="connections")

