from flask import Flask, Response, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return Response('Hello? Yes, this is dog!', status=200)

@app.route('/api', methods=['POST'])
def api():
    # content = request.json
    # Do something with the json content
    # For demonstration purposes, let's just send it back as the response
    # return jsonify(content)
    return Response('/API', status=200)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    print('Listening on port %s' % (port))
    app.run(host='0.0.0.0', port=port)