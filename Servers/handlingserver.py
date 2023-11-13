from flask import Flask, request, jsonify
import requests
from main import db, User, Log


app = Flask(__name__)

calculation_servers = ["http://localhost:8085", "http://localhost:8086", "http://localhost:8087"]
servers_loading = [0, 0, 0]
servers_queue = [[], [], []]
servers_working = [False, False, False]
handling_queue = False


@app.route('/choose', methods=['GET', 'POST'])
def calculate():
    print("got to /choose")
    min_server_index = servers_loading.index(min(servers_loading))
    data = request.get_json()
    servers_loading[min_server_index] += int(data["beer_count"])

    new_data = {
        "user_name": data["user_name"],
        "beer_count": data["beer_count"],
        "server": min_server_index
    }
    response = {
        "result": "Currently busy",
        "execution_time": 0
    }
    if servers_working[min_server_index]:
        print("Got to queueu handling")
        servers_queue[min_server_index].append(new_data)
        servers_loading[min_server_index] += int(data["beer_count"])
        response = queueuhandling()
        return response
    else:
        print("Got to normal handling")
        servers_working[min_server_index] = True
        response = requests.post(f"{calculation_servers[min_server_index]}/calculate", json=new_data)
        servers_working[min_server_index] = False
        return jsonify(response.json())


@app.route('/queueuhandling', methods=['GET'])
def queueuhandling():
    response = {"user_name": "a", "beer_count": 0, "result": "Yep", "execution_time": 0}
    user_name = "a"
    beer_count = 0
    calc_result = "Yep"
    execution_time = 0
    some_list = []
    for i in range(len(servers_queue)):
        if len(servers_queue[i]) > 0 and not servers_working[i]:
            print(f"Working in server {i + 1} from queueu")
            servers_working[i] = True
            data = servers_queue[i].pop(0)
            response = requests.post(f"{calculation_servers[i]}/calculate", json=data)
            user_name = response.json()["user_name"]
            beer_count = response.json()["beer_count"]
            calc_result = response.json()["result"]
            execution_time = response.json()["execution_time"]
            some_list.append({
                "user_name": user_name,
                "beer_count": beer_count,
                "result": calc_result,
                "execution_time": execution_time
            })
            servers_loading[data["server"]] -= int(data["beer_count"])

    if len(some_list) > 0:
        return some_list

    return jsonify(response)




if __name__ == '__main__':
    app.run(debug=True, port=8088)
