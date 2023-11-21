import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
calculation_servers = ["http://localhost:8085", "http://localhost:8086", "http://localhost:8087"]
main_server = "http://localhost:8080"


@app.route('/choose', methods=['POST'])
def choose():
    print("Got Request. Choosing on which server to send data")
    servers_load = []
    for i in range(len(calculation_servers) - 1):
        servers_load.append(int(requests.get(f"{calculation_servers[i]}/status").json()["load"]))

    min_load = servers_load.index(min(servers_load))

    print(f"Sending data to server {min_load + 1}")

    response = requests.post(f"{calculation_servers[min_load]}/postdata", json=request.get_json())

    print(f"Data was sent to server, Result: {response.json()['result']}")
    if response.json()["result"] == "success":
        return jsonify(response.json())
    return jsonify({"result": "failed"})


@app.route('/postdatafromserver', methods=['POST'])
def postdatafromserver():
    print("Got data from server")
    data = request.get_json()

    print("Sending data to main server")
    print(data)
    response = requests.post(f"{main_server}/retreiveresult", json=data)
    return jsonify({"result": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=8088)


