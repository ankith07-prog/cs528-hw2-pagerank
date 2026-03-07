from flask import Flask, request

app = Flask(__name__)

@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    print("FORBIDDEN REQUEST FROM", data, flush=True)
    return "received", 200

app.run(host="0.0.0.0", port=5001)
