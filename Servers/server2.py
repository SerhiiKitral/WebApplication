from flask import Flask, request, jsonify
from main import calculate_beer_drinking

app = Flask(__name__)


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    user_name = data["user_name"]
    beer_count = data["beer_count"]

    calc_result, execution_time = calculate_beer_drinking(user_name, beer_count)

    response_data = {
        "result": calc_result,
        "execution_time": execution_time
    }

    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, port=8086)
