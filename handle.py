import datetime
import requests
import json
import traceback
from bs4 import BeautifulSoup

HELP_MSG = \
"""命令格式:
    sem [free] [now]
    coater [now]
    bind <username> <password>"""

OEMT_HOST = 'http://127.0.0.1:11934'

SYNTAX_ERR_MSG = "无法识别┑(￣Д ￣)┍\n    输入[help]来查看可用命令"

EQUIP_ID = {
    'sem': '536e62ab-364f-478b-bf33-1e9015843ee6',
    'coater': '16a07cd3-f77b-42b5-81f8-21b7209d3a8d'
}

MAINTENENCE_MSG = "维护中.."

def handle_content(msg):
    try:
        text = msg.Content.decode()
        fromuser = msg.FromUserName
        args = text.split(' ')
        if len(args) == 1:
            if args[0].lower() == 'help':
                return HELP_MSG
        elif len(args) == 2:
            if args[1].lower() == 'now':
                return get_status(args[0].lower())
            elif args[1].lower() == 'free':
                return get_reserve_status(args[0].lower(), args[1].lower())
        elif len(args) == 3:
            if args[0].lower() == 'bind':
                return bind_user(fromuser, args[1], args[2])

        return SYNTAX_ERR_MSG

    except Exception as e:
        print(e)
        #traceback.print_exc()
        return "Internal Error"


def get_status(equipment):
    if equipment not in EQUIP_ID.keys():
        return SYNTAX_ERR_MSG
    try:
        resp_raw = requests.get(OEMT_HOST + '/Equipment/GetEquipmentCurStatusInfo?Id=' + EQUIP_ID[equipment], timeout=3)
    except requests.exceptions.Timeout:
        return MAINTENENCE_MSG
    resp = json.loads(resp_raw.text)
    return resp.get('Remark', 'Server Error, please try again.')

    
def get_reserve_status(equipment, day):
    if equipment != 'sem':
            return SYNTAX_ERR_MSG

    post_data = {
        'EquipmentId': EQUIP_ID[equipment],
        'equipmentTimeAppointmemtMode': '0',
        'WeekIndex': '0'
    }
    try:
        resp_raw = requests.post(OEMT_HOST + '/Equipment/AppointmentTimesContainer', data=post_data, timeout=3)
    except requests.exceptions.Timeout:
        return MAINTENENCE_MSG
    resrv_data = BeautifulSoup(resp_raw.text, "lxml").find(id="tbAppointmentTimes")
    #cur_date = str(datetime.date.today())
    #d1_date = str(datetime.date.today() + datetime.timedelta(days=1))
    #d2_date = str(datetime.date.today() + datetime.timedelta(days=2))
    #cur_day = str(datetime.date.today().weekday())
    free_periods = [item['title'] for item in resrv_data.find_all('td', 'valid')]
    free_periods.sort(key=lambda x:x[-2], reverse=True)
    tmp = []

    finished = False
    while not finished:
        # 压缩为简洁表达形式
        for i in range(0, len(free_periods)-1):
            if (free_periods[i].split('-')[1]).split('(')[0] == free_periods[i+1].split('-')[0] and \
                (free_periods[i].split('-')[1]).split('(')[1] == (free_periods[i+1].split('-')[1]).split('(')[1]:
                free_periods[i+1] = '-'.join([free_periods[i].split('-')[0], free_periods[i+1].split('-')[1]])
                free_periods.pop(i)
                break

        unfinished_count = 0
        for i in range(0, len(free_periods)-1):
            if (free_periods[i].split('-')[1]).split('(')[0] == free_periods[i+1].split('-')[0] and \
                (free_periods[i].split('-')[1]).split('(')[1] == (free_periods[i+1].split('-')[1]).split('(')[1]:
                unfinished_count += 1
        if unfinished_count == 0:
            finished = True

    if free_periods == []:
        return "全都约满啦╭翻桌～"

    return '空闲时段:\n' + '\n'.join(free_periods)

def bind_user(openid, username, passwd):

    post_data = {
        'HomeLoginType': '1',
        'LoginName': username,
        'LoginPassword': passwd,
        'IsRememberMe': 'true',
        'loginType': '1'
    }
    try:
        resp_raw = requests.post(OEMT_HOST + '/Account/LoginSubmit', data=post_data, timeout=3)
    except requests.exceptions.Timeout:
        return MAINTENENCE_MSG
    if resp_raw.text == '出错,用户名和密码不正确!':
        return "用户名密码错误(＞﹏＜)"

    try:
        with open('./users.json') as f:
            users = json.loads(f.read())
    except FileNotFoundError:
        users = {}
    users[openid] = [username, passwd]
    json.dump(users, open('./users.json', 'w'))

    return "绑定成功！"

def reserve_equip(openid, equipment, t_start, t_end):
    try:
        with open('./users.json') as f:
            users = json.loads(f.read())
    except FileNotFoundError:
        return "请先绑定用户名密码！" 
    if openid not in users.keys():
        return "请先绑定用户名密码！"

    username = users[openid][0]
    passwd = users[openid][1]

    post_data = {
        'HomeLoginType': '1',
        'LoginName': username,
        'LoginPassword': passwd,
        'IsRememberMe': 'true',
        'loginType': '1'
    }
    try:
        resp_raw = requests.post(OEMT_HOST + '/Account/LoginSubmit', data=post_data, timeout=3)
    except requests.exceptions.Timeout:
        return MAINTENENCE_MSG

    

