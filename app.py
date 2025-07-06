from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
from io import StringIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change for security

# ---------- INIT DATABASE ----------
def init_user_db():
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def init_student_db():
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT,
            dept TEXT,
            m1 INTEGER,
            m2 INTEGER,
            m3 INTEGER,
            total INTEGER,
            grade TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_user_db()
init_student_db()

# ---------- ROUTES ----------
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = sqlite3.connect('user.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('error.html', message='Username already exists.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            session['is_admin'] = (username == 'admin')
            return redirect('/')
        else:
            return render_template('error.html', message='Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session or not session.get('is_admin'):
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        dept = request.form['dept']
        m1, m2, m3 = int(request.form['m1']), int(request.form['m2']), int(request.form['m3'])
        total = m1 + m2 + m3
        grade = 'A' if total >= 250 else 'B' if total >= 200 else 'C'

        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO students (name, roll, dept, m1, m2, m3, total, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, roll, dept, m1, m2, m3, total, grade))
        conn.commit()
        conn.close()

        return render_template('result.html', name=name, roll=roll, dept=dept, m1=m1, m2=m2, m3=m3, total=total, grade=grade)
    return render_template('add_student.html')

@app.route('/view_students')
def view_students():
    if 'username' not in session:
        return redirect('/login')
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    conn.close()
    return render_template('view_students.html', students=students)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        return redirect('/login')
    student = None
    if request.method == 'POST':
        roll = request.form['roll']
        conn = sqlite3.connect('student.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE roll = ?', (roll,))
        student = cursor.fetchone()
        conn.close()
    return render_template('search.html', student=student)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect('/login')
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        dept = request.form['dept']
        m1, m2, m3 = int(request.form['m1']), int(request.form['m2']), int(request.form['m3'])
        total = m1 + m2 + m3
        grade = 'A' if total >= 250 else 'B' if total >= 200 else 'C'
        cursor.execute('''
            UPDATE students SET name=?, roll=?, dept=?, m1=?, m2=?, m3=?, total=?, grade=? WHERE id=?
        ''', (name, roll, dept, m1, m2, m3, total, grade, id))
        conn.commit()
        conn.close()
        return redirect('/view_students')
    cursor.execute('SELECT * FROM students WHERE id=?', (id,))
    student = cursor.fetchone()
    conn.close()
    return render_template('edit_student.html', student=student)

@app.route('/delete/<int:id>')
def delete(id):
    if 'username' not in session or not session.get('is_admin'):
        return redirect('/login')
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/view_students')

@app.route('/download')
def download():
    if 'username' not in session or not session.get('is_admin'):
        return redirect('/login')
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, roll, dept, m1, m2, m3, total, grade FROM students')
    students = cursor.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Roll', 'Department', 'Mark1', 'Mark2', 'Mark3', 'Total', 'Grade'])
    writer.writerows(students)
    output.seek(0)

    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=students.csv"})

@app.route('/error')
def error():
    return render_template('error.html', message="Something went wrong.")

# ---------- RUN SERVER ----------
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
