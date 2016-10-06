import time
import requests
import json
import traceback

HELP_MSG = \
"""Usage:
    sem <stats>
    coater <stats>"""

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
            if args[1].lower() == 'stats':
                return get_status(args[0].lower())
            elif args[1].lower() in ['d0', 'd1', 'd2']:
                return get_reserve_status(args[0].lower(), args[1].lower())

        return SYNTAX_ERR_MSG

    except Exception as e:
        print(e)
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
    with open('reserve.txt','w') as f:
        f.write(resp_raw.text)
    return "Success"

