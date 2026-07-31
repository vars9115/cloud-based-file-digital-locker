from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cloudlocker123"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cloudlocker'

mysql = MySQL(app)

# Upload Folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Home
@app.route('/')
def home():
    return render_template('index.html')


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
            (username, email, password)
        )
        mysql.connection.commit()
        cursor.close()

        flash("Registration Successful")
        return redirect('/login')

    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect('/dashboard')
        else:
            flash("Invalid Login")

    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM files WHERE user_id=%s",
        (session['user_id'],)
    )
    files = cursor.fetchall()

    return render_template(
        'dashboard.html',
        files=files,
        username=session['username']
    )


# Upload File
@app.route('/upload', methods=['POST'])
def upload():

    if 'user_id' not in session:
        return redirect('/login')

    file = request.files['file']

    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        size = os.path.getsize(path)

        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO files
               (user_id,file_name,file_path,file_size)
               VALUES(%s,%s,%s,%s)""",
            (session['user_id'], filename, path, size)
        )
        mysql.connection.commit()

        flash("File Uploaded Successfully")

    return redirect('/dashboard')


# Download File
@app.route('/download/<int:id>')
def download(id):

    from flask import send_file

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM files WHERE file_id=%s",
        (id,)
    )
    file = cursor.fetchone()

    return send_file(file['file_path'], as_attachment=True)


# Delete File
@app.route('/delete/<int:id>')
def delete(id):

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM files WHERE file_id=%s",
        (id,)
    )
    file = cursor.fetchone()

    if file:
        if os.path.exists(file['file_path']):
            os.remove(file['file_path'])

        cursor.execute(
            "DELETE FROM files WHERE file_id=%s",
            (id,)
        )
        mysql.connection.commit()

    flash("File Deleted")

    return redirect('/dashboard')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)