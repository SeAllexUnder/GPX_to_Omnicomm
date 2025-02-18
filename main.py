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
        print(parameters)
        login = parameters['login']
        pwd = parameters['password']
        cell_dir = parameters['folder']
        type_zone = parameters['type']
        lineWidth = parameters['lineWidth']
    omnicomm = Omnicomm(login, pwd)
    files_list = [f for f in glob.glob('*') if '.gpx' in f]
    result_all = []
    error_count = 0
    if not omnicomm.get_jwt():
        raise Exception(get_time_now() + ' - ' + 'Ошибка авторизации')
    geozones_tree = omnicomm.get_geozone_tree()
    mother_group_id = geozones_tree['autocheck_id']
    cell_group_id = None
    current_geofences = []
    for c in geozones_tree['children']:
        if c['name'] == cell_dir:
            cell_group_id = c['autocheck_id']
            current_geofences += [o['name'].replace(' ', '') for o in c['objects']]
            break
    if cell_group_id is None:
        raise Exception(f'Ошибка! Целевая группа "{cell_dir}" не найдена в Omnicomm Online!')
    geozones = {}
    print('Считываю .gpx')
    for file in files_list:
        tree = ET.parse(file)
        root = tree.getroot()
        for child in root:
            if 'trk' in child.tag:
                name_in_param = f'{files_list.index(file)+1}. '
                for param in child:
                    if 'name' in param.tag:
                        name_in_param += param.text
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
    print('Создаю геозоны')
    for geozone in geozones:
        name, points = geozone, geozones[geozone]
        print(name)
        result = omnicomm.create_geofence(name, points, type_z=type_zone, lineWidth=lineWidth)
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
        result_move = omnicomm.geofence_move(mother_group_id, cell_group_id, geofence_id)
        if result_move.status_code == 200:
            result_all.append(get_time_now() + ' - ' + name + f'- Геозона помещена в группу "{cell_dir}"')
        else:
            result_all.append(get_time_now() + ' - ' + name + f'- Ошибка перемещения в группу "{cell_dir}" (4283): '
                              + result_move.text)
            error_count += 1
            continue
    result_all.append(get_time_now() + ' - ' + 'Ошибок: ' + str(error_count))
    with open('Лог.txt', 'w', encoding='utf-8') as res:
        res.write('\n'.join(result_all))


try:
    main()
except Exception as _ex:
    print(_ex)
    input()
