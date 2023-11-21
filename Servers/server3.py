from flask import Flask, request, jsonify
from main import calculate_beer_drinking, handling_server
from flask_sqlalchemy import SQLAlchemy
import time
import requests
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///server3.db'
db = SQLAlchemy(app)


class ServerStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loading = db.Column(db.Integer, default=0)


class QueueEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    beer_count = db.Column(db.Integer)
    server_id = db.Column(db.Integer, db.ForeignKey('server_status.id'))
    server = db.relationship('ServerStatus', backref=db.backref('queue_entries', lazy=True))


@app.route('/status', methods=['GET', 'POST'])
def status():
    print("Getting status")
    server_status = ServerStatus.query.all()[0]
    print(f"Status got: {server_status.loading}")
    return jsonify({"load": server_status.loading})


@app.route('/postdata', methods=['POST'])
def postdata():
    print("Putting data in queue")

    data = request.get_json()
    user_name = data["user_name"]
    beer_count = data["beer_count"]

    # Add the new entry to the queue
    server_status = ServerStatus.query.all()[0]
    server_status.loading += beer_count
    db.session.add(QueueEntry(user_name=user_name, beer_count=beer_count, server_id=0))
    db.session.commit()

    print("Data was put in queue")
    return jsonify({"result": "success"})


def calculate():
    with app.app_context():
        while True:
            print("Calculating")

            queue_entry = QueueEntry.query.order_by(QueueEntry.id).first()

            if queue_entry is not None:
                user_name = queue_entry.user_name
                beer_count = queue_entry.beer_count

                server_status = ServerStatus.query.get(queue_entry.server_id)
                server_status.loading -= beer_count
                db.session.delete(queue_entry)
                db.session.commit()

                calc_result, execution_time = calculate_beer_drinking(user_name, beer_count)

                response_data = {
                    "user_name": user_name,
                    "beer_count": beer_count,
                    "result": calc_result,
                    "execution_time": execution_time
                }

                print("Sending data to handling server")
                response = requests.post(f"{handling_server}/postdatafromserver", json=response_data)

            time.sleep(2)


def print_database_values():
    server_statuses = ServerStatus.query.all()
    queue_entries = QueueEntry.query.all()

    print("Server Statuses:")
    for status in server_statuses:
        print(f"ID: {status.id}, Loading: {status.loading}")

    print("\nQueue Entries:")
    for entry in queue_entries:
        print(f"ID: {entry.id}, User Name: {entry.user_name}, Beer Count: {entry.beer_count}, Server ID: {entry.server_id}")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print_database_values()
    monitoring_thread = threading.Thread(target=calculate)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    app.run(debug=True, port=8087)
