import sqlite3
import os
from flask import Flask, request, g, render_template, send_file, flash

# Use absolute path for the database
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example.db')
print(f"Database path: {DATABASE}")

app = Flask(__name__)
app.config['DATABASE'] = DATABASE
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

def connect_to_database():
    """Connect to SQLite database."""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        print(f"Connected to database: {app.config['DATABASE']}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def get_db():
    """Get database connection, or create one if it doesn’t exist."""
    if 'db' not in g:
        g.db = connect_to_database()
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection when the request ends."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def execute_query(query, args=(), commit=False):
    """Execute a SQL query and return results."""
    db = get_db()
    cur = db.cursor()
    try:
        print(f"Executing query: {query} with args: {args}")
        cur.execute(query, args)
        if commit:
            db.commit()
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
        raise
    finally:
        cur.close()

def init_db():
    """Initialize the database and create tables if they don’t exist."""
    with app.app_context():
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS users (
                    Username TEXT PRIMARY KEY,
                    Password TEXT NOT NULL,
                    firstname TEXT NOT NULL,
                    lastname TEXT NOT NULL,
                    email TEXT NOT NULL,
                    count INTEGER
                )
            """, commit=True)
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")

# Initialize the database when the application starts
init_db()

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username and password:
            result = execute_query("SELECT firstname, lastname, email, count FROM users WHERE Username = ? AND Password = ?", (username, password))
            if result:
                return responsePage(*result[0])
            else:
                message = 'Invalid Credentials!'
        else:
            message = 'Please enter Credentials'

    return render_template('index.html', message=message)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        email = request.form.get('email', '').strip()
        uploaded_file = request.files.get('textfile')

        if username and password and firstname and lastname and email:
            result = execute_query("SELECT 1 FROM users WHERE Username = ?", (username,))
            if result:
                message = 'User has already registered!'
            else:
                word_count = getNumberOfWords(uploaded_file) if uploaded_file else None
                execute_query("INSERT INTO users (username, password, firstname, lastname, email, count) VALUES (?, ?, ?, ?, ?, ?)",
                              (username, password, firstname, lastname, email, word_count), commit=True)

                result = execute_query("SELECT firstname, lastname, email, count FROM users WHERE Username = ?", (username,))
                if result:
                    return responsePage(*result[0])
        else:
            message = 'Some of the fields are missing!'

    return render_template('registration.html', message=message)

@app.route("/download")
def download():
    path = "Limerick.txt"
    return send_file(path, as_attachment=True)

def getNumberOfWords(file):
    """Count words in an uploaded file."""
    if file:
        try:
            data = file.read().decode('utf-8')
            words = data.split()
            return len(words)
        except UnicodeDecodeError:
            flash("Invalid file format. Please upload a text file.")
            return None
    return None

response_page_css = """
<style>
.response-container {
    max-width: 600px;
    margin: 20px auto;
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.response-container h2 {
    text-align: center;
    margin-bottom: 20px;
}

.response-container p {
    margin-bottom: 10px;
}

.response-container a {
    display: block;
    text-align: center;
    margin-top: 20px;
    text-decoration: none;
    color: #007bff;
}
</style>
"""

def responsePage(firstname, lastname, email, count):
    return f"""
    <html>
    <head>
        <title>User Information</title>
        {response_page_css}
    </head>
    <body>
        <div class="response-container">
            <h2>User Information</h2>
            <p><strong>First Name:</strong> {firstname}</p>
            <p><strong>Last Name:</strong> {lastname}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Word Count:</strong> {count if count is not None else "N/A"}</p>
            <a href="/download">Download</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
