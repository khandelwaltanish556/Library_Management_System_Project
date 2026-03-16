from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from datetime import date

app = Flask(__name__)
app.secret_key = "library_secret_key_123"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library_db'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('index.html')   # Ye main page open karega

from MySQLdb.cursors import DictCursor

# Edit_book
@app.route('/edit_book/<int:id>')
def Edit_book(id):

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cur.fetchone()

    return render_template('edit_book.html', book=book)


# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",(username,password))
        mysql.connection.commit()
        return redirect('/')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]   # 🔥 YAHI MAIN LINE HAI
            return redirect('/dashboard')
        else:
            return "Invalid Credentials"

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    return render_template('dashboard.html', books=books)

# Add Book
@app.route('/add_book', methods=['GET','POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        quantity = request.form['quantity']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO books(title,author,quantity) VALUES(%s,%s,%s)",(title,author,quantity))
        mysql.connection.commit()
        return redirect('/dashboard')
    return render_template('add_book.html')

# Issue Book
from datetime import date

from datetime import date, timedelta

@app.route('/issue_book/<int:id>')
def issue_book(id):

    user_id = session.get('user_id')   # ✅ Safe method
    if not user_id:
      return redirect('/login')  # Login nahi to login bhejo

    issue_date = date.today()
    return_date = issue_date + timedelta(days=7)

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO issued_books(user_id, book_id, issue_date, return_date)
        VALUES (%s,%s,%s,%s)
    """, (user_id, id, issue_date, return_date))

    cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=%s", (id,))

    mysql.connection.commit()

    return redirect('/dashboard')   # 🔥 Yaha dashboard hi hona chahiye

#all_issued_book
from datetime import date

@app.route('/all_issued_books')
def all_issued_books():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            users.username,                -- row[0]
            users.id,                      -- row[1]
            books.title,                   -- row[2]
            issued_books.issue_date,       -- row[3]
            issued_books.return_date,      -- row[4]
            issued_books.actual_return_date, -- row[5]
            issued_books.fine,             -- row[6]
            issued_books.id                -- row[7]
        FROM issued_books
        JOIN users ON users.id = issued_books.user_id
        JOIN books ON books.id = issued_books.book_id
    """)

    records = cur.fetchall()

    from datetime import date
    return render_template("all_issued.html", records=records, today=date.today())


from datetime import date, timedelta

@app.route('/return_book/<int:id>')
def return_book(id):

    cur = mysql.connection.cursor()

    cur.execute("SELECT issue_date, return_date, book_id FROM issued_books WHERE id=%s", (id,))
    record = cur.fetchone()

    if not record:
        return "Record Not Found"

    issue_date = record[0]
    return_date = record[1]
    book_id = record[2]

    today = date.today()
    fine = 0

    # ✅ Agar return_date NULL hai to 10 din baad ka bana do
    if return_date is None:
        return_date = issue_date + timedelta(days=10)

    # ✅ Safe fine calculation
    if today > return_date:
        days_late = (today - return_date).days
        fine = days_late * 10

    cur.execute("""
        UPDATE issued_books
        SET actual_return_date=%s,
            return_date=%s,
            fine=%s
        WHERE id=%s
    """, (today, return_date, fine, id))

    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=%s", (book_id,))
    mysql.connection.commit()

    return redirect('/all_issued_books')
@app.route('/logout')
def logout():
    session.clear()   # ✅ pura session delete
    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)