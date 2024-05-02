import asyncio
import websockets
from cryptography.fernet import Fernet
import cv2
import base64
import numpy as np
from ultralytics import YOLO
import json


# define some constants
CONFIDENCE_THRESHOLD = 0.8
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


def decode_frame(encoded_frame):
    # Декодирование строки из формата base64
    decoded_bytes = base64.b64decode(encoded_frame)
    # Преобразование байтов в массив numpy
    nparr = np.frombuffer(decoded_bytes, np.uint8)
    # Декодирование изображения с помощью cv2.imdecode()
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame


# Создание объекта для вычитания фона
backSub = cv2.createBackgroundSubtractorMOG2()


# load the pre-trained YOLOv8n model
model = YOLO("yolov8n.pt")

def frame_neuro_processing(frame):
    results = model.track(source=frame, persist=True)
    annotated_frame = results[0].plot()
    return annotated_frame
    # Обнаружение объектов на кадре с помощью модели YOLOv8n
    results = model(frame)
    return frame

min_shadow = 180
max_shadow = 255
# Определение порога минимальной площади контура
min_contour_area = 500



def frame_processing(frame):
    frame_initial = frame.copy()
    # Копирование исходного кадра для отрисовки
    frame_out = frame.copy()
    # Преобразование изображения в оттенки серого
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Вычитание фона
    fg_mask = backSub.apply(frame)
    # Устанавливаем глобальный порог для удаления теней
    retval, mask_thresh = cv2.threshold(fg_mask, min_shadow, max_shadow, cv2.THRESH_BINARY)
    # Поиск контуров
    contours, _ = cv2.findContours(mask_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Вычисление ядра
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    # Применение эрозии
    mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)
    # Фильтрация контуров по минимальной площади
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    white_image = np.full_like(frame_out, (255, 255, 255), dtype=np.uint8)
    # Отрисовка прямоугольников вокруг больших контуров
    for cnt in large_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        white_image[y:y+h, x:x+w] = frame_initial[y:y+h, x:x+w]
        frame_out = cv2.rectangle(frame_out, (x, y), (x+w, y+h), (0, 0, 200), 3)
        # Отображаем прямоугольник и подписываем его меткой класса
    # Отображение результата

    return frame_out, white_image

async def receive_from_server(websocket, path, key):
    cipher_suite = Fernet(key)
    while True:
        try:
            # Подключение к серверу на порту 9998
            async with websockets.connect('ws://localhost:9998') as server_websocket:
                instructions = None
                while True:
                    try:
                        # Получение данных от сервера на порту 9998
                        data = await server_websocket.recv()
                        # Дешифровка данных
                        data = cipher_suite.decrypt(data).decode()
                        # Обработка данных
                        frame = decode_frame(data)  # Декодируем данные
                        frame, cropped = frame_processing(frame)     # Обрабатываем кадр
                        # Преобразование кадра в строку base64
                        data = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')

                        # Создание словаря с данными для JSON
                        json_data = {
                            "video_image": data
                        }

                        if instructions != None and json.loads(instructions).get('recognize'):
                            json_data["recognize_image"] = base64.b64encode(cv2.imencode('.jpg', frame_neuro_processing(cropped))[1]).decode('utf-8')
                            # json_data["recognize_image"] = base64.b64encode(cv2.imencode('.jpg', cropped)[1]).decode('utf-8')

                        # Преобразование словаря в JSON-строку
                        data = json.dumps(json_data)
                        # Пересылка данных клиенту на порту 9999
                        await websocket.send(data)

                        #получение данных от клиента (веб-браузера)
                        instructions = await websocket.recv()
                        if instructions:
                            # print("Получены инструкции:", instructions)
                            # Попытка парсинга JSON
                            try:
                                parsed_instructions = json.loads(instructions)
                                # print("Разобранные инструкции:", parsed_instructions)
                                min_shadow = parsed_instructions.get('min_shadow')
                                max_shadow = parsed_instructions.get('max_shadow')
                                min_contour_area = parsed_instructions.get('min_contour_area')
                                recognize = parsed_instructions.get('recognize')
                                if recognize:
                                    print("Запрошено распознавание движущихся объектов")
                                # Далее вы можете обрабатывать распарсированные данные
                                # Например, выполнить какие-то действия на основе полученных инструкций
                            except json.JSONDecodeError:
                                print("Ошибка при парсинге JSON.")
                        else:
                            print("Пустой ответ от клиента.")

                    except websockets.exceptions.ConnectionClosedError:
                        print("Соединение с сервером на порту 9998 закрыто. Переподключение...")
                        break
                    except Exception as e:
                        # Логирование и обработка других исключений
                        print(f"Произошла ошибка: {e}")
                        break
        except websockets.exceptions.ConnectionClosedError: #было ConnectionError
            print("Не удалось подключиться к серверу на порту 9998. Повторная попытка через 1 секунду...")
            await asyncio.sleep(1)
        except Exception as e:
            # Логирование и обработка других исключений
            print(f"Произошла ошибка: {e}")
            await asyncio.sleep(1)

key = b'2na2SazDd926u9bR5Sn5MBJBsuIsyANgdKERwhyBmag='

async def main(websocket, path):
    await receive_from_server(websocket, path, key)

start_server = websockets.serve(main, "localhost", 9999)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
