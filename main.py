import csv
import io
from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import time
import requests

app = Flask(__name__, template_folder="HTML")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_data.db'
db = SQLAlchemy(app)

calculation_servers = ["http://localhost:8085", "http://localhost:8086", "http://localhost:8087"]
current_server_index = 0


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_logged_in = db.Column(db.Boolean, default=False)


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(120), nullable=False)
    execution_time = db.Column(db.Float, nullable=False)
    result = db.Column(db.String(10), nullable=False)
    number_of_beers = db.Column(db.Integer, nullable=False)


app.secret_key = 'your_secret_key'


def calculate_beer_drinking(user_name, beer_count):
    start_time = time.time()
    calc_result = "success"

    for i in range(beer_count * 10000000):
        if i > 10 * 100000000:
            calc_result = "timeout"
            break
        if i % 50000000 == 0:
            elapsed_time = time.time() - start_time
            if elapsed_time > 15:
                calc_result = "timeout"
                break

    execution_time = time.time() - start_time

    return calc_result, execution_time


@app.route('/solve', methods=['POST'])
def solve():
    global current_server_index
    execution_time = 0
    beer_count = int(request.form['beer'])
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user_name = user.email

            server_url = calculation_servers[current_server_index]
            current_server_index = (current_server_index + 1) % len(calculation_servers)

            try:
                response = requests.post(f"{server_url}/calculate",
                                         json={"user_name": user_name, "beer_count": beer_count})
                if response.status_code == 200:
                    data = response.json()
                    calc_result = data["result"]
                    execution_time = data.get("execution_time", 0)
                else:
                    calc_result = "error"
            except Exception as e:
                calc_result = "error"

            log_entry = Log(user_name=user_name, execution_time=execution_time, result=calc_result,
                            number_of_beers=beer_count)
            db.session.add(log_entry)
            db.session.commit()

            return render_template('index.html', result_="Result: " + calc_result)

    return render_template('index.html',)


@app.route('/index')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))


@app.route('/')
def start():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('register.html', error_message="User already exists")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(email=email, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = ""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session['user_id'] = user.id
                user.is_logged_in = True
                db.session.commit()
                return redirect(url_for('index'))
            else:
                error_message = "Password is incorrect"
        else:
            error_message = "User is not found"

    return render_template('login.html', error_message=error_message)


@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.is_logged_in = False
            db.session.commit()
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/download_csv')
def download_csv():
    user_id = session.get('user_id')

    if not user_id:
        return "No user session found."

    user = User.query.get(user_id)

    if not user:
        return "User not found."

    logs = Log.query.filter_by(user_name=user.email).all()

    if not logs:
        return "No data to export."

    response = Response(generate_csv(logs), content_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=data.csv"

    return response


def generate_csv(logs):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User Name", "Execution Time", "Result", "Number of Beers"])

    for log in logs:
        writer.writerow([log.user_name, log.execution_time, log.result, log.number_of_beers])

    return output.getvalue()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8080)
