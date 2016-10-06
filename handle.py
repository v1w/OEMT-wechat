import datetime
import requests
import json
import traceback
from bs4 import BeautifulSoup

HELP_MSG = \
"""Usage:
    sem <free> <now>
    coater <now>"""

OEMT_HOST = 'http://127.0.0.1:11934'

SYNTAX_ERR_MSG = "Syntax Error\n    Use [help] to list available commands."

EQUIP_ID = {
    'sem': '536e62ab-364f-478b-bf33-1e9015843ee6',
    'coater': '16a07cd3-f77b-42b5-81f8-21b7209d3a8d'
}


def handle_content(content):
    try:
        args = content.split(' ')
        if len(args) == 1:
            if args[0].lower() == 'help':
                return HELP_MSG
        elif len(args) == 2:
            if args[1].lower() == 'now':
                return get_status(args[0].lower())
            elif args[1].lower() == 'free':
                return get_reserve_status(args[0].lower(), args[1].lower())

        return SYNTAX_ERR_MSG

    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Internal Error"


def get_status(equipment):
    if equipment not in EQUIP_ID.keys():
        return SYNTAX_ERR_MSG

    resp_raw = requests.get(OEMT_HOST + '/Equipment/GetEquipmentCurStatusInfo?Id=' + EQUIP_ID[equipment], timeout=4)
    resp = json.loads(resp_raw.text)
    return resp.get('Remark', 'OEMT-Server Error, please try again.')

    
def get_reserve_status(equipment, day):
    if equipment != 'sem':
            return SYNTAX_ERR_MSG

    post_data = {
        'EquipmentId': EQUIP_ID[equipment],
        'equipmentTimeAppointmemtMode': '0',
        'WeekIndex': '0'
    }

    resp_raw = requests.post(OEMT_HOST + '/Equipment/AppointmentTimesContainer', data=post_data, timeout=4)
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


    return '\n'.join(free_periods)

    

