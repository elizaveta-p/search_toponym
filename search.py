import sys
from io import BytesIO
# Этот класс поможет нам сделать картинку из потока байт
from pprint import pprint
import sys
from distance import lonlat_distance
from PyQt5 import uic  # Импортируем uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow
import requests
from PIL import Image
from PIL.ImageQt import ImageQt
from features import count_spn


class MyWidget(QMainWindow):
    def __init__(self, image, text):
        super().__init__()
        uic.loadUi('ui_form.ui', self)  # Загружаем дизайн
        # Обратите внимание: имя элемента такое же как в QTDesigner
        self.change_pic(image, text)

    def change_pic(self, image: Image.Image, text):
        self.a = ImageQt(image)
        self.pixmap = QPixmap.fromImage(self.a)
        self.pic.setPixmap(self.pixmap)
        self.textBrowser.setText(text)
        # Имя элемента совпадает с objectName в QTDesigner


geocoder_apikey = "40d1649f-0493-4b70-98ba-98533de7710b"
search_apikey = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"


# Пусть наше приложение предполагает запуск:
# python search.py Москва, ул. Ак. Королева, 12
# Тогда запрос к геокодеру формируется следующим образом:
toponym_to_find = " ".join(sys.argv[1:])
# toponym_to_find = 'США, Фишерсвилл'
# toponym_to_find = "Москва, ул. Ак. Королева, 12"

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {
    "apikey": geocoder_apikey,
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
# pprint(json_response)
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
toponym_longitude, toponym_lattitude = float(toponym_longitude), float(toponym_lattitude)
coord1, coord2 = toponym['boundedBy']['Envelope']['lowerCorner'].split(' '), \
                 toponym['boundedBy']['Envelope']['upperCorner'].split(' ')

# coord1 = [float(x) for x in coord1]
# coord2 = [float(x) for x in coord2]
# spn = count_spn(coord1, coord2)
# delta = "0.005"


search_api_server = "https://search-maps.yandex.ru/v1/"
search_params = {
    "apikey": search_apikey,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": f"{toponym_longitude},{toponym_lattitude}",
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)
if not response:
    #...
    pass


json_response = response.json()
pprint(json_response)
# Получаем первую найденную организацию.
pts = [f"{toponym_longitude},{toponym_lattitude},pm2rdm"]
information = []
for i in range(len(json_response["features"])):
    organization = json_response["features"][i]
    # Название организации.
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    # Адрес организации.
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    if "Hours" not in organization['properties']['CompanyMetaData'].keys():
        color = "gr"
    elif 'TwentyFourHours' in organization['properties']['CompanyMetaData']["Hours"]['Availabilities'][0].keys():
        color = 'gn'
    else:
        color = 'bl'

    # Получаем координаты ответа.
    point = organization["geometry"]["coordinates"]
    org_point = "{0},{1}".format(point[0], point[1])

    # spn = count_spn([toponym_longitude, toponym_lattitude], point)
    pt = f"{org_point},pm2{color}m"
    pts.append(pt)
    snippet = {
        "имя": org_name,
        "адрес": org_address,
        "расстояние": str(lonlat_distance([float(toponym_longitude), float(toponym_lattitude)],
                                          [float(point[0]), float(point[1])]) // 1000) + ' км'
    }

    snippet = '\n'.join(['\n'.join([f"{x}: ", snippet[x]]) for x in snippet.keys()])
    information.append(snippet)
    if i == 10:
        break
pts = '~'.join(pts)
information = '\n\n'.join(information)
# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    # "spn": spn,
    "l": "map",
    "pt": pts
}

map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)

bytes_im = BytesIO(response.content)
im = Image.open(bytes_im)
# print(im.size)
# im.show()
app = QApplication(sys.argv)
ex = MyWidget(im, information)
ex.show()
sys.exit(app.exec_())
# Создадим картинку
# и тут же ее покажем встроенным просмотрщиком операционной системы