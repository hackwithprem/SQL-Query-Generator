from flask import Flask, request, jsonify
from backend.services.query_service import execute_query

app = Flask(__name__)


@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()

    sql = data.get("sql")

    if not sql:
        return jsonify({
            "success": False,
            "error": "SQL query is required."
        }), 400

    result = execute_query(sql)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)