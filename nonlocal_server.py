import asyncio
import websockets
from cryptography.fernet import Fernet
import cv2
import base64
import numpy as np

backSub = cv2.createBackgroundSubtractorMOG2()

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

def frame_processing(frame):
    # Вычитание фона
    fg_mask = backSub.apply(frame)
    # Устанавливаем глобальный порог для удаления теней
    retval, mask_thresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)
    # Поиск контуров
    contours, _ = cv2.findContours(mask_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Вычисление ядра
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    # Применение эрозии
    mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)
    # Определение порога минимальной площади контура
    min_contour_area = 500  
    # Фильтрация контуров по минимальной площади
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    # Копирование исходного кадра для отрисовки
    frame_out = frame.copy()
    # Отрисовка прямоугольников вокруг больших контуров
    for cnt in large_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        frame_out = cv2.rectangle(frame_out, (x, y), (x+w, y+h), (0, 0, 200), 3)
    # Отображение результата
    return frame_out

async def receive_from_server(websocket, path, key):
    cipher_suite = Fernet(key)
    while True:
        try:
            # Подключение к серверу на порту 9998
            async with websockets.connect('ws://localhost:9998') as server_websocket:
                while True:
                    try:
                        # Получение данных от сервера на порту 9998
                        data = await server_websocket.recv()
                        # Дешифровка данных
                        data = cipher_suite.decrypt(data).decode()
                        # Обработка данных
                        frame = decode_frame(data)  # Декодируем данные
                        frame = frame_processing(frame)     # Обрабатываем кадр
                        # Преобразование кадра в строку base64
                        data = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8') 
                        # Пересылка данных клиенту на порту 9999
                        await websocket.send(data)
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
