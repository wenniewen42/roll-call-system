from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 學生資料表
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer)
    student_id = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)  # 學號
    email = db.Column(db.String(120), unique=True, nullable=False)      # 電子郵件
    password = db.Column(db.String(80), nullable=False)                 # 密碼（需進一步加密）
    courses = db.relationship('Course', secondary='student_courses', back_populates='students')
    attendances = db.relationship('Attendance', back_populates='student')

# 教授資料表
class Professor(db.Model):
    __tablename__ = 'professors'
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.String(20), unique=True, nullable=False)  # 教職員編號
    email = db.Column(db.String(120), unique=True, nullable=False)        # 電子郵件
    password = db.Column(db.String(80), nullable=False)                   # 密碼（需進一步加密）
    courses = db.relationship('Course', back_populates='professor')

# 課程資料表
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)                      # 課程名稱
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'))  # 授課教授
    professor = db.relationship('Professor', back_populates='courses')
    students = db.relationship('Student', secondary='student_courses', back_populates='courses')
    pins = db.relationship('PinData', back_populates='course')
    attendance_dates = db.relationship('AttendanceDate', back_populates='course')

# 學生與課程的多對多關係表
class StudentCourses(db.Model):
    __tablename__ = 'student_courses'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    course_name = db.Column(db.String(20), db.ForeignKey('courses.name'), primary_key=True)

# PIN 碼資料表
class PinData(db.Model):
    __tablename__ = 'pin_data'
    pin = db.Column(db.String(6), nullable=False, primary_key=True)                        # PIN 碼
    course_name = db.Column(db.String(20), db.ForeignKey('courses.name'))       # 對應課程
    course = db.relationship('Course', back_populates='pins')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 創建時間

# 點名日期表
class AttendanceDate(db.Model):
    __tablename__ = 'attendance_dates'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)                           # 點名日期
    course_name = db.Column(db.String(20), db.ForeignKey('courses.name'))      # 對應課程
    course = db.relationship('Course', back_populates='attendance_dates')
    attendances = db.relationship('Attendance', back_populates='attendance_date')
    __table_args__ = (db.UniqueConstraint('course_name', 'date', name='unique_course_date'),)

# 點名紀錄表
class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))     # 學生
    attendance_date_id = db.Column(db.Integer, db.ForeignKey('attendance_dates.id'))  # 點名日期
    attendance_date = db.relationship('AttendanceDate', back_populates='attendances')
    student = db.relationship('Student', back_populates='attendances')
    status = db.Column(db.String(20), nullable=False, default='Absent')  # 出席狀態（出席/缺席）
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)   # 點名時間
