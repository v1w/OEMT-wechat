from flask import Flask, url_for, request
import hashlib
app = Flask(__name__)

@app.route('/wx', methods=['GET', 'POST'])
def wx():
    if request.method == 'GET':
        try:
            data = request.args
            token = "welcomeOEMT"
            if len(data) == 0:
                return ""

            raw = [token, data['timestamp'], data['nonce']]
            raw.sort()
            sha1 = hashlib.sha1()
            for i in raw:
                sha1.update(i.encode())
            hashcode = sha1.hexdigest()

            if hashcode == data['signature']:
                return data['echostr']
            else:
                return ""
        except Exception:
            return ""

    else:
        try:
            data = request.args
            print(data)
            return "OK"
        except Exception:
            return ""



if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)