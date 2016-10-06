# -*- coding:utf-8 -*- 
from flask import Flask, request
import receive, reply
import handle

app = Flask(__name__)

@app.route('/wx', methods=['POST','GET'])
def wx():
    if request.method == 'GET':
        return "Not Allowed"
    if request.content_type != 'text/xml':
        return "Not Allowed"
    try:
        data = request.get_data()
        #print("Handle POST data:\n" + data)
        recMsg = receive.parse_xml(data)
        if isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'text':
                toUser = recMsg.FromUserName
                fromUser = recMsg.ToUserName
                send_content = handle.handle_content(recMsg.Content.decode())
                replyMsg = reply.TextMsg(toUser, fromUser, send_content)
                return replyMsg.send()
        else:
            return "success"
    except Exception:
        return ""


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)