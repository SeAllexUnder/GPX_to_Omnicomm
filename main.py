import glob
import xml.etree.ElementTree as ET
import time
import json
# from tqdm import tqdm
from datetime import datetime
from Omnicomm import Omnicomm


def get_time_now():
    time_now = datetime.utcfromtimestamp(int(time.time()) + 10800).strftime("%Y-%m-%d %H:%M:%S")
    return time_now


def main():
    with open('parameters.json') as p:
        parameters = json.load(p)
        login = parameters['login']
        pwd = parameters['password']
    omnicomm = Omnicomm(login, pwd)
    files_list = [f for f in glob.glob('*') if '.gpx' in f]
    result_all = []
    error_count = 0
    geozones = {}
    print('Считываю .gpx')
    for file in files_list:
        tree = ET.parse(file)
        root = tree.getroot()
        for child in root:
            if 'trk' in child.tag:
                name_in_param = ''
                for param in child:
                    if 'name' in param.tag:
                        name_in_param = param.text
                    geozones[name_in_param] = []
                    if 'trkseg' in param.tag:
                        for point in param:
                            if 'lat' in point.attrib.keys() and 'lon' in point.attrib.keys():
                                coordinates = {
                                    "latitude": point.attrib['lat'],
                                    "longitude": point.attrib['lon']
                                }
                                geozones[name_in_param].append(coordinates)
            # if 'lat' in child.attrib.keys() and 'lon' in child.attrib.keys():
            #     coordinates = {
            #         "latitude": child.attrib['lat'],
            #         "longitude": child.attrib['lon']
            #     }
            #     points.append(coordinates)
    if omnicomm.get_jwt():
        print('Создаю геозоны')
        for geozone in geozones:
            name, points = geozone, geozones[geozone]
            print(name)
            result = omnicomm.create_geofence(name, points)
            if result.status_code == 200:
                result_all.append(get_time_now() + ' - ' + name + '- Геозона создана')
            else:
                result_all.append(get_time_now() + ' - ' + name + '- Ошибка при создании геозоны: ' + result.text)
                error_count += 1
                continue
            geofence_uuid = result.json()['uuid'][0]
            result_get_info = omnicomm.get_geofence_info(geofence_uuid)
            if result_get_info.status_code == 200:
                result_all.append(get_time_now() + ' - ' + name + '- Получен id геозоны')
            else:
                result_all.append(get_time_now() + ' - ' + name + '- Ошибка получения id: ' + result_get_info.text)
                error_count += 1
                continue
            geofence_id = result_get_info.json()['id']
            result_move = omnicomm.geofence_move(466, 4283, geofence_id)
            if result_move.status_code == 200:
                result_all.append(get_time_now() + ' - ' + name + '- Геозона помещена в группу "Конвертер"')
            else:
                result_all.append(get_time_now() + ' - ' + name + '- Ошибка перемещения в группу "Конвертер" (4283): '
                                  + result_move.text)
                error_count += 1
                continue
        result_all.append(get_time_now() + ' - ' + 'Ошибок: ' + str(error_count))
    else:
        result_all.append(get_time_now() + ' - ' + 'Ошибка авторизации')
    with open('Лог.txt', 'w', encoding='utf-8') as res:
        res.write('\n'.join(result_all))


try:
    main()
except Exception as _ex:
    print(_ex)
    input()
