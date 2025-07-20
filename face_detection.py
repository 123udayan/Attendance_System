import cv2
import numpy as np
import face_recognition
import mysql.connector
from datetime import datetime
import os

# --- Load known faces from database ---
conn = mysql.connector.connect(
    host='localhost', user='root', password='Password@123', database='attendancefiles')
mycursor = conn.cursor()
mycursor.execute("SELECT name, Picture FROM Total_students")
data = mycursor.fetchall()
conn.close()

images = []
classNames = []

for row in data:
    name, img_path = row

    if isinstance(img_path, bytes):
        img_path = img_path.decode()

    if os.path.exists(img_path):
        cur_img = cv2.imread(img_path)
        if cur_img is not None:
            images.append(cur_img)
            classNames.append(name)
        else:
            print(f"Failed to read image: {img_path}")
    else:
        print(f"File not found: {img_path}")

def find_encodings(images):
    encode_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)
        if encodings:
            encode_list.append(encodings[0])
    return encode_list

available_faces = find_encodings(images)
print("Loaded encodings for:", classNames)

last_attendance_date = {}

def markattendance(name):
    conn = mysql.connector.connect(
        host='localhost', user='root', password='Password@123', database='attendancefiles')
    mycursor = conn.cursor()
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%I:%M:%S %p')

    if name not in last_attendance_date or last_attendance_date[name] != date:
        sql = "INSERT INTO present_students (name, time, date) VALUES (%s, %s, %s)"
        values = (name, time, date)
        mycursor.execute(sql, values)
        last_attendance_date[name] = date

        update_status_query = "UPDATE Total_students SET status = %s WHERE name = %s"
        mycursor.execute(update_status_query, ('Present', name))
        conn.commit()
        status_text = f"Attendance marked for {name} on {date}"
    else:
        status_text = f"Attendance already marked for {name} on {date}"

    conn.close()
    return status_text

def find_absent_students(class_names):
    conn = mysql.connector.connect(
        host='localhost', user='root', password='Password@123', database='attendancefiles')
    mycursor = conn.cursor()
    mycursor.execute("SELECT DISTINCT name FROM present_students")
    present_names = set(name[0] for name in mycursor.fetchall())
    absent_students = list(set(class_names) - present_names)

    now = datetime.now()
    date = now.strftime('%Y-%m-%d')

    for name in absent_students:
        mycursor.execute("SELECT 1 FROM absent_students WHERE name = %s AND date = %s", (name, date))
        if not mycursor.fetchone():
            sql = "INSERT INTO absent_students (name, date) VALUES (%s, %s)"
            values = (name, date)
            mycursor.execute(sql, values)

            update_status_query = "UPDATE Total_students SET status = %s WHERE name = %s"
            mycursor.execute(update_status_query, ('Absent', name))
            conn.commit()

    conn.close()
    return absent_students

# --- Start webcam for live face recognition ---
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    img_small = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    faces_cur_frame = face_recognition.face_locations(img_small)
    encodes_cur_frame = face_recognition.face_encodings(img_small, faces_cur_frame)

    for encode_face, face_loc in zip(encodes_cur_frame, faces_cur_frame):
        matches = face_recognition.compare_faces(available_faces, encode_face)
        face_distances = face_recognition.face_distance(available_faces, encode_face)
        match_index = np.argmin(face_distances) if len(face_distances) else -1

        if match_index != -1 and matches[match_index]:
            name = classNames[match_index]
            top, right, bottom, left = face_loc
            top, right, bottom, left = int(top*4), int(right*4), int(bottom*4), int(left*4)
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 3)
            cv2.putText(img, name, (left, top-10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
            status_text = markattendance(name)
            cv2.putText(img, status_text, (left, bottom+30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0), 2)

    cv2.imshow('Face Recognition Attendance', img)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to quit
        break

cap.release()
cv2.destroyAllWindows()

# After loop ends
absent_students = find_absent_students(classNames)
print("Absent students:", absent_students)
