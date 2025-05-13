from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api', methods=['POST'])
def api_endpoint():
    data = request.get_json()
    # Verarbeite die Anfrage
    return jsonify({"message": "Erfolg", "data": data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
