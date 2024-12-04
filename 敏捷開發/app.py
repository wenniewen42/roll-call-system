from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Student, Professor, PinData, Course, Attendance, AttendanceDate
from config import Config
from flask_cors import CORS
import qrcode
import io
import base64
import random
import time
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}}, supports_credentials=True)
#Session(app)

# 初始化資料庫
db.init_app(app)
with app.app_context():
    db.create_all()

# with app.app_context():
#     # 創建一個測試用戶
#     test_user = Student(student_id="22334", email="testtest@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256'))
#     db.session.add(test_user)
#     db.session.commit()

# with app.app_context():
#     # 檢查並插入教授資料
#     if not Professor.query.filter_by(email="prof1@gmail.com").first():
#         professor1 = Professor(professor_id="P001", email="prof1@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256'))
#         professor2 = Professor(professor_id="P002", email="prof2@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256'))
#         db.session.add_all([professor1, professor2])
#         db.session.commit()

#     # 檢查並插入學生資料
#     if not Student.query.filter_by(email="student1@gmail.com").first():
#         students = [
#             Student(student_id="S001", email="student1@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256')),
#             Student(student_id="S002", email="student2@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256')),
#             Student(student_id="S003", email="student3@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256')),
#             Student(student_id="S004", email="student4@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256')),
#             Student(student_id="S005", email="student5@gmail.com", password=generate_password_hash("password", method='pbkdf2:sha256')),
#         ]
#         db.session.add_all(students)
#         db.session.commit()

#     # 檢查並插入課程資料
#     if not Course.query.filter_by(name="程式語言").first():
#         course1 = Course(name="程式語言", professor_id=1)  # 確保 ID 與資料庫對應
#         course2 = Course(name="軟體工程", professor_id=1)
#         course3 = Course(name="資料結構", professor_id=2)
#         db.session.add_all([course1, course2, course3])
#         db.session.commit()

#     # 配置學生與課程
#     course1 = Course.query.filter_by(name="程式語言").first()
#     course2 = Course.query.filter_by(name="軟體工程").first()
#     course3 = Course.query.filter_by(name="資料結構").first()

#     if course1 and not course1.students:
#         course1.students.extend(students[:3])
#     if course2 and not course2.students:
#         course2.students.extend(students[2:])
#     if course3 and not course3.students:
#         course3.students.extend(students)

#     db.session.commit()

with app.app_context():
    # 查詢 AttendanceDate 和 Attendance 表的所有記錄
        attendance_dates = AttendanceDate.query.all()  # 取得所有 AttendanceDate 紀錄
        attendances = Attendance.query.all()  # 取得所有 Attendance 紀錄

        # 準備資料以便於輸出
        attendance_data = []

        # 將 AttendanceDate 和 Attendance 資料結合起來
        for attendance_date in attendance_dates:
            date_info = {
                'date': attendance_date.date,
                'course_name': attendance_date.course_name,
                'attendances': []
            }

            # 為每個 AttendanceDate 加入相應的 Attendance 記錄
            for attendance in attendances:
                if attendance.attendance_date_id == attendance_date.id:
                    date_info['attendances'].append({
                        'student_id': attendance.student_id,
                        'status': attendance.status,
                        'timestamp': attendance.timestamp
                    })

            attendance_data.append(date_info)
        print('data: ',attendance_data)

    # # 刪除依賴表資料（Attendance）
    # db.session.query(Attendance).delete()

    # # 刪除主表資料（AttendanceDate）
    # db.session.query(AttendanceDate).delete()

    # # 提交更改
    # db.session.commit()

    #print("All records have been deleted.")
        
    # attendance = Attendance.query.all()
    # for attendances in attendance:
    #     print(attendances.student_id, attendances.attendance_date_id, attendances.status)
        #print(attendances)

#     courses = Course.query.all()
#     for course in courses:
#         print(course.name, course.professor.email)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    student_id = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    # 驗證密碼
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

    # 驗證是否已存在
    existing_student = Student.query.filter(
        (Student.student_id == student_id) | (Student.email == email)
    ).first()
    if existing_student:
        return jsonify({'success': False, 'message': 'Student ID or email already registered'}), 400

    # 新增學生
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_student = Student(student_id=student_id, email=email, password=hashed_password)
    db.session.add(new_student)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user_type = data.get("user_type")  # 使用者類型: 'student' 或 'professor'

    if user_type == "student":
        # 查找學生
        student = Student.query.filter_by(student_id=username).first()
        if not student:
            return jsonify({"success": False, "message": "Student account does not exist"}), 404
        if not check_password_hash(student.password, password):
            return jsonify({"success": False, "message": "Wrong account or password"}), 401

        return jsonify({"success": True, 'student_id': username, "message": "Student login successful"})

    elif user_type == "professor":
        # 查找教授
        professor = Professor.query.filter_by(professor_id=username).first()
        if not professor:
            return jsonify({"success": False, "message": "Professor account does not exist"}), 404
        if not check_password_hash(professor.password, password):
            return jsonify({"success": False, "message": "Wrong account or password"}), 401
        
        return jsonify({"success": True, "message": "Professor logged in successfully"})

    else:
        return jsonify({"success": False, "message": "Unknown user type"}), 400
    
@app.route('/generate-pin', methods=['POST'])
def generate_pin():
    try:
        data = request.json
        course_name = data.get('course_name')
        if not course_name:
            return jsonify({'success': False, 'message': 'Course name is required'}), 400

        # 隨機生成 PIN 碼
        pin = random.randint(100000, 999999)
        timestamp = datetime.utcnow()  # 當前時間戳
        
        # 查詢是否已經存在該課程名稱的 PIN 碼
        existing_pin = PinData.query.filter_by(course_name=course_name).first()
        
        if existing_pin:
            # 如果已經存在，則更新現有記錄
            existing_pin.pin = pin
            existing_pin.created_at = timestamp
            db.session.commit()  # 更新數據庫
        else:
            # 如果沒有該課程，則創建新記錄
            new_pin = PinData(pin=pin, course_name=course_name, created_at=timestamp)
            db.session.add(new_pin)
            db.session.commit()  # 提交到數據庫

        # 生成 QR Code(還沒完全設定好!!!)
        qr = qrcode.make(f"PIN: {pin}")
        img_io = io.BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # 將 QR Code 編碼為 base64 並返回
        img_b64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        if not img_b64:
            raise Exception("QR Code encoding to base64 failed")
        qr_code_url = f"data:image/png;base64,{img_b64}"

        # 生成與課程相關的 AttendanceDate 紀錄
        date_today = datetime.utcnow().date()  # 獲取當前日期
        existing_attendance_date = AttendanceDate.query.filter_by(course_name=course_name, date=date_today).first()

        if not existing_attendance_date:
            # 如果該日期的點名紀錄不存在，創建新的 AttendanceDate 紀錄
            new_attendance_date = AttendanceDate(course_name=course_name, date=date_today)
            db.session.add(new_attendance_date)
            db.session.commit()

            # 獲取該課程的所有學生
            course = Course.query.filter_by(name=course_name).first()
            if course:
                # 為所有選修該課程的學生創建 Attendance 紀錄，默認缺席
                for student in course.students:
                    new_attendance = Attendance(
                        student_id=student.student_id,
                        attendance_date_id=new_attendance_date.id,
                        status='Absent',  # 默認缺席
                    )
                    db.session.add(new_attendance)

                # 提交所有 Attendance 紀錄到數據庫
                db.session.commit()

        print('pin: ', pin)

        return jsonify({
            'success': True,
            'pin': pin,
            'qr_code_url': qr_code_url,
            'message': 'PIN generated successfully'
        })
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({'success': False, 'message': f'Error occurred: {str(e)}'}), 500


@app.route('/validate-attendance', methods=['POST'])
def validate_attendance():
    try:
        data = request.json
        pin = data.get('pin')
        student_id = data.get('student_id')

        # 1. 根據 pin 獲取對應的課程名稱 (course_name)
        pin_data = PinData.query.filter_by(pin=pin).first()

        if not pin_data:
            return jsonify({'success': False, 'message': 'Invalid PIN'})

        course_name = pin_data.course_name
        print('course_name: ', course_name)

        # 2. 查找該課程和日期的點名記錄
        date = datetime.utcnow().date()  # 使用當前日期作為點名日期
        course = Course.query.filter_by(name=course_name).first()  # 查找課程
        print('course: ', course)
        if not course:
            return jsonify({'success': False, 'message': 'Course not found'})

        attendance_date = AttendanceDate.query.filter_by(course_name=course_name, date=date).first()
        print('attendance_date.date: ', attendance_date.date, 'attendance_date :', attendance_date)
        if not attendance_date:
            return jsonify({'success': False, 'message': 'Invalid roll call date'})

        # 3. 驗證學生是否屬於該課程
        student = Student.query.filter_by(student_id=student_id).first()
        print('student: ', student)
        if not student or course_name not in [course.name for course in student.courses]:
            return jsonify({'success': False, 'message': 'This student does not belong to this course and cannot be named'})

        # 4. 查找該學生的點名記錄
        print('AttendanceDate.course_name: ', attendance_date.course_name)
        attendance_record = db.session.query(Attendance).join(AttendanceDate).join(Course).filter(
            Attendance.student_id == student_id,
            AttendanceDate.course_name == course_name,
            Course.name == course_name,  # 確保是正確的課程
            Attendance.attendance_date_id == attendance_date.id  # 確保是正確的日期
        ).first()
        print('attendance_record: ', attendance_record)
        if not attendance_record:
            return jsonify({'success': False, 'message': 'The roll call record of this student was not found and the roll call cannot be made.'})

        # 5. 更新點名狀態為出席
        if attendance_record.status == 'Present':
            return jsonify({'success': False, 'message': 'You have already called your name'})

        attendance_record.status = 'Present'
        attendance_record.timestamp = datetime.utcnow()

        # 提交更改
        db.session.commit()

        return jsonify({'success': True, 'message': 'The roll call was successful!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Roll call failed, please try again later', 'error': str(e)})

@app.route('/get-courses', methods=['GET'])
def get_courses():
    try:
        # 從會話中取得已登入的使用者資料
        user_id = request.args.get('user_id')
        user_type = request.args.get('user_type')

        if not user_type or not user_id:
            return jsonify({'success': False, 'message': 'Not logged in, please log in first'}), 401

        if user_type == 'student':
            # 查找學生
            student = Student.query.filter_by(student_id=user_id).first()
            if not student:
                return jsonify({'success': False, 'message': 'student does not exist'}), 404
            
            # 取得學生選修的課程清單
            courses = student.courses
            course_list = [{'id': course.id, 'name': course.name} for course in courses]

        elif user_type == 'professor':
            # 查找教授
            professor = Professor.query.filter_by(professor_id=user_id).first()
            if not professor:
                return jsonify({'success': False, 'message': 'Professor does not exist'}), 404
            
            # 取得教授教授的課程清單
            courses = professor.courses
            course_list = [{'id': course.id, 'name': course.name} for course in courses]

        else:
            return jsonify({'success': False, 'message': 'Unknown user type'}), 400

        return jsonify({'success': True, 'courses': course_list})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
