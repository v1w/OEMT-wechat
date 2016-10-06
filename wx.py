# -*- coding:utf-8 -*- 
from flask import Flask, request
import receive, reply
import handle
import traceback

app = Flask(__name__)

@app.route('/wx', methods=['POST','GET'])
def wx():
    if request.method == 'GET':
        return "Not Allowed"
    if request.content_type != 'text/xml':
        return "Not Allowed"
    try:
        data = request.get_data()
        recMsg = receive.parse_xml(data)
        if isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'text':
            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName
            send_content = handle.handle_content(recMsg)
            replyMsg = reply.TextMsg(toUser, fromUser, send_content)
            return replyMsg.send()
        elif isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'event':
            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName
            send_content = "欢迎您，新用户！\n目前支持的功能：查询SEM当前使用状态或可预约时间段\n开发中：SEM预约\n为方便查找，请置顶本公众号\n" + handle.HELP_MSG
            replyMsg = reply.TextMsg(toUser, fromUser, send_content)
            return replyMsg.send()
        else:
            return "success"
    except Exception as e:
        #traceback.print_exc()
        return ""


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)