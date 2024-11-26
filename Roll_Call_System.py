import sqlite3
import random
import time
import qrcode
from PIL import Image
import pyzbar.pyzbar as pyzbar

# 初始化數據庫
def init_db():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # 學生表
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT
        )
    ''')

    # 教師表
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            name TEXT,
            password TEXT
        )
    ''')

    # 點名 PIN 表
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS attendance_pin (
            pin TEXT PRIMARY KEY,
            created_at TIMESTAMP
        )
    ''')

    # 出席紀錄表
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            pin TEXT,
            status TEXT,  -- "present", "absent", "late"
            date TIMESTAMP, 
            FOREIGN KEY(student_id) REFERENCES students(student_id),
            FOREIGN KEY(pin) REFERENCES attendance_pin(pin)
        )
    ''')

    conn.commit()
    conn.close()

# 教師發布 PIN 碼
def generate_pin():
    pin = str(random.randint(1000, 9999))
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("INSERT INTO attendance_pin (pin, created_at) VALUES (?, ?)", (pin, time.time()))
    conn.commit()
    conn.close()
    return pin

# 學生登錄並輸入 PIN
def student_attendance(student_id, pin):
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # 檢查學生是否存在
    c.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = c.fetchone()
    if not student:
        print("學生未註冊，請先註冊！")
        conn.close()
        return

    # 檢查 PIN 是否有效
    c.execute("SELECT * FROM attendance_pin WHERE pin = ?", (pin,))
    valid_pin = c.fetchone()
    if not valid_pin:
        print("無效的 PIN 碼！")
        conn.close()
        return

    # 紀錄出席
    c.execute("INSERT INTO attendance_records (student_id, pin, status, date) VALUES (?, ?, ?, ?)", 
              (student_id, pin, "present", time.time()))
    conn.commit()
    conn.close()
    print("出席紀錄已提交！")

# 教師查看出席紀錄
def view_teacher_attendance():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute('''
        SELECT s.student_id, s.name, r.pin, r.status, r.date
        FROM attendance_records r
        JOIN students s ON r.student_id = s.student_id
    ''')

    records = c.fetchall()
    conn.close()

    print("學生出席紀錄：")
    for record in records:
        print(f"學號: {record[0]}, 姓名: {record[1]}, 出席 PIN: {record[2]}, 狀態: {record[3]}, 日期: {record[4]}")

# 註冊學生
def register_student(student_id, name):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT student_id FROM students WHERE student_id = ?", (student_id,))
    result = c.fetchone()

    if result:
        print(f"學生ID {student_id} 已经存在，無法註冊!")
    else:
        # 插入新学生
        c.execute("INSERT INTO students (student_id, name) VALUES (?, ?)", (student_id, name))
        conn.commit()
        print(f"學生 {name} 註冊成功！")
    conn.close()

# 註冊教師
def register_teacher(teacher_id, name, password):
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()
    c.execute("INSERT INTO teachers (teacher_id, name, password) VALUES (?, ?, ?)", (teacher_id, name, password))
    conn.commit()
    conn.close()
    print("教師註冊成功！")

# 學生查看歷史出席紀錄
def view_student_attendance_history(student_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT date, status FROM attendance_records WHERE student_id = ?", (student_id,))
    records = c.fetchall()

    if records:
        print("出席歷史紀錄：")
        for record in records:
            print(f"日期: {record[0]}, 狀態: {record[1]}")
    else:
        print("沒有找到出席紀錄。")
    
    conn.close()

# 批量標記全班出席（教師功能）
def mark_attendance_for_class(date, status, student_ids):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    for student_id in student_ids:
        c.execute("INSERT INTO attendance_records (student_id, status, date) VALUES (?, ?, ?)", 
                  (student_id, status, date))

    conn.commit()
    print(f"已成功批量標記 {len(student_ids)} 名學生的出席情况。")

    conn.close()

# 生成QR Code
def generate_qr_code_for_attendance(date, teacher_id):
    qr_data = f"attendance:{date}:{teacher_id}"
    qr = qrcode.make(qr_data)
    qr.save(f"attendance_qr_{date}.png")
    print(f"已生成QR Code，保存为 'attendance_qr_{date}.png'")

# 學生掃描 QR Code
def scan_qr_code(image_path):
    img = Image.open(image_path)
    decoded_objects = pyzbar.decode(img)
    
    if not decoded_objects:
        print("未能掃描到 QR Code")
        return

    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')
        print("扫描到的 QR Code 数据:", qr_data)

        qr_parts = qr_data.split(":")
        if qr_parts[0] == "attendance" and len(qr_parts) == 3:
            date = qr_parts[1]
            teacher_id = qr_parts[2]
            print(f"日期: {date}, 教师 ID: {teacher_id}")

            student_id = input("請輸入您的學號：")

            mark_student_attendance(student_id, date, teacher_id)
        else:
            print("QR Code 格式不正確！")


# 學生掃碼點名後系統完成點名
def mark_student_attendance(student_id, date, teacher_id):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student = c.fetchone()
    if not student:
        print("學生未註冊，請先註冊！")
        conn.close()
        return

    c.execute("SELECT * FROM attendance_records WHERE student_id = ? AND date = ?", (student_id, date))
    existing_record = c.fetchone()
    if existing_record:
        print(f"學生 {student_id} 今天的出席已經紀錄過了。")
        conn.close()
        return

    c.execute("INSERT INTO attendance_records (student_id, date, status) VALUES (?, ?, ?)", 
              (student_id, date, "present"))
    conn.commit()
    print(f"學生 {student_id} 於 {date} 出席，已標記為 'present'。")
    
    conn.close()



    

if __name__ == "__main__":
    init_db()

    while True:
        print("\n歡迎使用出勤系统！")
        print("1. 學生註冊")
        print("2. 教師註冊")
        print("3. 教師發布 PIN")
        print("4. 學生提交出席")
        print("5. 教師查看出席紀錄")
        print("6. 教師發布 QR Code")
        print("7. 學生查看歷史出席紀錄")
        print("0. 退出")
        choice = input("請輸入選項: ")

        if choice == "1":
            student_id = input("請輸入學號: ")
            name = input("請輸入姓名: ")
            register_student(student_id, name)
        elif choice == "2":
            teacher_id = input("請輸入教師帳號: ")
            name = input("請輸入姓名: ")
            password = input("請輸入密碼: ")
            register_teacher(teacher_id, name, password)
        elif choice == "3":
            pin = generate_pin()
            print(f"發布的 PIN 碼是: {pin}")
        elif choice == "4":
            student_id = input("請輸入學號: ")
            pin = input("請輸入 PIN 碼: ")
            student_attendance(student_id, pin)
        elif choice == "5":
            view_teacher_attendance()
        elif choice == "6":
            date = input("請輸入日期（格式：YYYY-MM-DD）: ")
            teacher_id = input("請輸入教師ID: ")
            generate_qr_code_for_attendance(date, teacher_id)
        elif choice == "7":
            student_id = input("請輸入學號: ")
            view_student_attendance_history(student_id) 
        elif choice == "0":
            print("退出系统！")
            break
        else:
            print("無效選項，請重試！")

