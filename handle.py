import datetime
import requests
import json
import traceback
from bs4 import BeautifulSoup
import re

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

MAINTAINENCE_MSG = "维护中.."


class Session(object):        
    def __init__(self, username, passwd):
        self.post_data = {
            'HomeLoginType': '1',
            'LoginName': username,
            'LoginPassword': passwd,
            'IsRememberMe': 'true',
            'loginType': '1'
        }
        resp_raw = requests.post(OEMT_HOST + '/Account/LoginSubmit', data=self.post_data, timeout=3)

        self.cookies = resp_raw.cookies


def handle_content(msg):
    try:
        text = msg.Content.decode()
        fromuser = msg.FromUserName
        args = text.split(' ')
        if len(args) == 1:
            if args[0].lower() == 'help':
                return HELP_MSG
            if args[0].lower() == 'debug':
                return reserve_equip(fromuser, 'sem', 1, 2)
        elif len(args) == 2:
            if args[1].lower() == 'now':
                return get_status(args[0].lower())
            elif args[1].lower() == 'free':
                return get_reserve_status(args[0].lower(), args[1].lower())
        elif len(args) == 3:
            if args[0].lower() == 'bind':
                return bind_user(fromuser, args[1], args[2])
        elif len(args) == 10:
            if args[1] == 'res':
                return reserve_equip(fromuser, args[0].lower(), int(args[3]), args[5], float(args[7]), args[9])

        return SYNTAX_ERR_MSG

    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Internal Error"


def get_status(equipment):
    if equipment not in EQUIP_ID.keys():
        return SYNTAX_ERR_MSG
    try:
        resp_raw = requests.get(OEMT_HOST + '/Equipment/GetEquipmentCurStatusInfo?Id=' + EQUIP_ID[equipment], timeout=3)
    except requests.exceptions.Timeout:
        return MAINTAINENCE_MSG
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
        return MAINTAINENCE_MSG
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
        return MAINTAINENCE_MSG
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

def reserve_equip(openid, equipment, date, t_start, duration, comment):
    try:
        with open('./users.json') as f:
            users = json.loads(f.read())
    except FileNotFoundError:
        return "请先绑定用户名密码！" 
    if openid not in users.keys():
        return "请先绑定用户名密码！"
    if equipment not in EQUIP_ID.keys():
        return "无法识别的仪器名称！"

    username = users[openid][0]
    passwd = users[openid][1]

    appoint_periods_num = int(duration/0.5)
    if appoint_periods_num <= 0:
        return "最小预约单位为半小时！"
    appoint_start = list(map(int, t_start.split(':')))
    if appoint_start[1] not in [0,30]:
        return "不允许预约非整数时间段！"
    start_min = appoint_start[0] * 60 + appoint_start[1]
    periods = [datetime.datetime.strptime(str(datetime.date.today()), '%Y-%m-%d') + datetime.timedelta(days=date, minutes=start_min + 30 * i) \
                for i in range(0, appoint_periods_num)]
    appoint_times = ','.join([period.strftime('%Y-%m-%d %H:%M') for period in periods])
    print(appoint_times)

    try:
        session = Session(username, passwd)
        post_data = {
        'equipmentTimeAppointmemtMode': '0',
        'equipmentId': EQUIP_ID[equipment],
        'userId': None,
        'changeAppointmentId': None,
        'date': None
        }
        resp_raw = requests.post(OEMT_HOST + '/Appointment/AppointmentUserRelativeInfo', data=post_data, timeout=3, cookies=session.cookies)
        m = re.search(r'"Id":".*?"', resp_raw.text)
        subject_id = m.group(0)[6:][:-1]
        post_data = {
        'SubjectId': subject_id,
        'UseNature': '0',
        'ExperimentationContent': comment,
        'isSelectTimeScope': 'false',
        'AppointmentStep': '30',
        'AppointmentTimes': appoint_times,
        'EquipmentId': EQUIP_ID[equipment],
        'AppointmentFeeTips': 'false'
        }
        resp_raw = requests.post(OEMT_HOST + '/Appointment/Appointment', data=post_data, timeout=3, cookies=session.cookies)
        m = re.search(r'出错', resp_raw.text)
        if m is not None:
            return resp_raw.text
        else:
            return "预约成功！"
    except requests.exceptions.Timeout:
        return MAINTAINENCE_MSG

    



    

