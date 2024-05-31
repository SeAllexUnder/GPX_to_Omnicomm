import json
import requests as r
from datetime import datetime
import time


class Omnicomm:
    URL = 'https://online.omnicomm.ru'
    jwt = ''
    login = ''
    pwd = ''

    def __init__(self, login, password):
        self.login = login
        self.pwd = password

    def get_jwt(self):
        '''
        Получение идентификатора сессии
        :return: результат начала сессии
        '''
        params = {'jwt': 1}
        URL = f'{self.URL}/auth/login'
        data = {'login': self.login, 'password': self.pwd}
        try:
            response = r.post(url=URL, params=params, data=data).json()
            self.jwt = f'JWT {response["jwt"]}'
            if self.jwt != '':
                return True
            else:
                return False
        except KeyError:
            return False

    def get_allVehicles(self):
        URL = f'{self.URL}/ls/api/v2/tree/vehicle'
        headers = {
            'Authorization': self.jwt
        }
        response = r.get(url=URL, headers=headers).json()
        return response

    def get_consolidated_report(self, vehIDs, startDate, stopDate):
        '''
        Выполнение сводного отчета
        :param vehIDs: список айди ТС
        :param startDate: UNIX дата начала
        :param stopDate: UNIX дата окончания
        :return: результат отчета
        '''
        print(f'Сводный отчет по {len(vehIDs)} ТС')
        if startDate > stopDate:
            raise Exception('get_consolidated_report - Некорректный период отчета - дата окончания больше даты начала')
        if len(vehIDs) == 0:
            raise Exception('get_consolidated_report - Не выбрано ни одно ТС')
        URL = f'{self.URL}/service/reports/'
        headers = {'Accept': 'application/json', 'Authorization': self.jwt}
        data = {"type": "ASEReport",
                "sync": 1,
                "rebuild": True,
                "tz": "Europe/Moscow",
                "params": {"from": startDate*1000,
                           "to": stopDate*1000,
                           "params": {"ID": vehIDs,
                                      "action": "getReportData",
                                      "fromDatetime": startDate*1000,
                                      "locale": "ru",
                                      "newui": True,
                                      "objectClass": [1 for _ in vehIDs],
                                      "objectType": ["FAS" for _ in vehIDs],
                                      "page": 1,
                                      "repConfigId": 5774,
                                      "reportFromdate": startDate*1000,
                                      "reportTodate": stopDate*1000,
                                      "rows": 100,
                                      "selectedRoots": ["FAS"],
                                      "sidx": "vehicleGrouped",
                                      "sord": "asc",
                                      "summerOffset": 180,
                                      "toDatetime": stopDate*1000,
                                      "tz": "Europe/Moscow",
                                      "userID": 477,
                                      "vehicleID": vehIDs,
                                      "winterOffset": 180},
                           "url": "consolidatedreport",
                           "method": "POST",
                           "traditional": True}}
        response = r.post(url=URL, headers=headers, json=data)
        return response.json()

    def get_vehicles_tree(self):
        URL = f'{self.URL}/ls/api/v1/tree/vehicle'
        headers = {
            'Authorization': self.jwt
        }
        response = r.get(url=URL, headers=headers).json()
        return response

    def create_geofence(self, name: str, points, color='#005824'):
        """
        :param name: имя геозоны
        :param points: массив точек геозоны в формате json {"latitude": int, "longitude": int}
        :param color: цвет геозоны
        :return: результат
        """
        URL = f'{self.URL}/api/service/geozones/geozones'
        headers = {'Accept': 'application/json', 'Authorization': self.jwt}
        params = {'type': 'json'}
        data = {
        "name": name,
        "color": color,
        "transparency": 50,
        "allowedSpeed": 60,
        "useAsAddress": True,
        "enableSpeedMonitoring": False,
        "status": 1,
        "geozoneType": 1,
        "radius": 0,
        "lineWidth": 50,
        "latitude": 0,
        "longitude": 0,
        "geometry": {
          "geometryType": 1,
          "points": points
            }
        }
        response = r.post(url=URL, headers=headers, json=data, params=params)
        return response

    def get_geofence_info(self, uuid):
        URL = f'{self.URL}/api/service/geozones/geozone/{uuid}'
        headers = {
            'Authorization': self.jwt
        }
        response = r.get(url=URL, headers=headers)
        return response

    def geofence_move(self, group_id_from, group_id_to, geofence_id):
        URL = f'{self.URL}/ls/api/v1/tree/geozone/move'
        headers = {'Accept': 'application/json', 'Authorization': self.jwt}
        data = {
            "action": 'moveObjects',
            "newParentGroupID": group_id_to,
            "objectsToMove": [
                {
                    "groupID": group_id_from,
                    "objectID": geofence_id
                }
            ]
        }
        response = r.post(url=URL, headers=headers, json=data)
        return response


def getVehicles_onGroup(groupInfo):
    vehIDs_list = []
    for ob in groupInfo['objects']:
        vehIDs_list.append(ob['terminal_id'])
    if len(groupInfo['children']) != 0:
        for child in groupInfo['children']:
            vehIDs_list += getVehicles_onGroup(child)
    return list(set(vehIDs_list))
    # else:
    #     return list(set(vehIDs_list))


if __name__ == '__main__':
    with open('parameters.json') as p:
        parameters = json.load(p)
        login = parameters['login']
        pwd = parameters['password']
    omnicomm = Omnicomm(login, pwd)
    if omnicomm.get_jwt():
        print('Создание геозоны тест')
        test_points = [
            {
                "latitude": 63.67540966719389,
                "longitude": 43.538518538698554
            },
            {
                "latitude": 63.675958765670657,
                "longitude": 43.539830474182963
            },
            {
                "latitude": 63.676503002643585,
                "longitude": 43.542129546403885
            },
            {
                "latitude": 63.672932060435414,
                "longitude": 43.542647548019886
            },
            {
                "latitude": 63.673129118978977,
                "longitude": 43.5380326397717
            },
            {
                "latitude": 63.675415869802237,
                "longitude": 43.538516610860825
            },
        ]
        result = omnicomm.create_geofence('test python', test_points)
        print(result.json())
        geofence_id = omnicomm.get_geofence_info(result.json()['uuid'][0]).json()['id']
        print(geofence_id)
        move_result = omnicomm.geofence_move(466, 4283, geofence_id)
        print(move_result.status_code)
