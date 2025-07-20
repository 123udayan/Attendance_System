import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Password@123',
    database='attendancefiles'
)
mycursor = conn.cursor()

# Step 1: Create the tables if they don't exist
mycursor.execute('''
CREATE TABLE IF NOT EXISTS Total_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    picture VARCHAR(255)
)
''')

mycursor.execute('''
CREATE TABLE IF NOT EXISTS present_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    date DATE
)
''')

# Step 2: Insert multiple students (only if not already added)
mycursor.execute("SELECT COUNT(*) FROM Total_students")
count = mycursor.fetchone()[0]

if count == 0:
    students = [
        ("Udayan", "images/udayan.jpg"),
        ("Yethin", "images/yethin.jpg"),
        ("Student2", "images/student2.jpg"),
        ("Student3", "images/student3.jpg")
    ]

    mycursor.executemany("INSERT INTO Total_students (name, picture) VALUES (%s, %s)", students)
    print(f"{len(students)} students inserted into Total_students.")
else:
    print("Students already exist in the database.")

# Save changes and close connection
conn.commit()
conn.close()
