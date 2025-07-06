from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret_key_123"  # Needed for session

# Function to calculate total, average, grade
def compute_results(marks):
    total = sum(marks)
    average = total / len(marks)
    if average >= 90:
        grade = 'A'
    elif average >= 75:
        grade = 'B'
    elif average >= 60:
        grade = 'C'
    elif average >= 50:
        grade = 'D'
    else:
        grade = 'F'
    return total, average, grade

# -------------- Register --------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open("users.txt", "a") as f:
            f.write(f"{username},{password}\n")
        return redirect('/login')
    return render_template('register.html')

# -------------- Login --------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with open("users.txt", "r") as f:
                for line in f:
                    user, pwd = line.strip().split(",")
                    if user == username and pwd == password:
                        session['user'] = username
                        return redirect('/')
        except FileNotFoundError:
            pass
        return render_template('error.html', message="Invalid username or password.")
    return render_template('login.html')

# -------------- Logout --------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# -------------- Home / Dashboard --------------
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html', user=session['user'])

# -------------- Add Student --------------
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        roll = request.form['roll']
        name = request.form['name']
        marks = [int(request.form[f'mark{i}']) for i in range(1, 6)]
        total, average, grade = compute_results(marks)
        with open("students.txt", "a") as f:
            f.write(f"{roll},{name},{','.join(map(str, marks))},{total},{average:.2f},{grade}\n")
        return render_template("result.html", roll=roll, name=name, marks=marks,
                               total=total, average=average, grade=grade)
    return render_template('add_student.html')

# -------------- View All Students --------------
@app.route('/view')
def view_students():
    if 'user' not in session:
        return redirect('/login')
    students = []
    try:
        with open("students.txt", "r") as f:
            for line in f:
                data = line.strip().split(",")
                students.append(data)
    except FileNotFoundError:
        pass
    return render_template('view_students.html', students=students)

# -------------- Search Student --------------
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        roll = request.form['roll']
        try:
            with open("students.txt", "r") as f:
                for line in f:
                    data = line.strip().split(",")
                    if data[0] == roll:
                        return render_template('result.html',
                            roll=data[0], name=data[1],
                            marks=data[2:7], total=data[7],
                            average=data[8], grade=data[9])
        except FileNotFoundError:
            pass
        return render_template('error.html', message="Student not found.")
    return render_template('search.html')

# -------------- Error Page --------------
@app.route('/error')
def error():
    return render_template('error.html', message="Something went wrong.")

# -------------- Run Server --------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

