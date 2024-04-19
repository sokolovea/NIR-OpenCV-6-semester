import asyncio
import cv2
import websockets
import base64
import argparse
from OpenSSL import crypto, SSL

# Функция для обработки видеопотока
async def video_stream(websocket, path, video_source):
    cap = cv2.VideoCapture(video_source)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Преобразование кадра в строку base64
        encoded_frame = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')

        # Отправка кадра серверу
        await websocket.send(encoded_frame)

# Парсинг аргументов командной строки
parser = argparse.ArgumentParser(description='Video streaming client')
parser.add_argument('--source', default=0, help='Video source (0 for webcam, path to file for file)')
args = parser.parse_args()

# Подключение к серверу и передача видеопотока
async def connect_to_server(video_source):
    uri = "ws://localhost:9998"  # Замените на адрес вашего сервера
    async with websockets.connect(uri) as websocket:
        await video_stream(websocket, '', video_source)

# Создание контекста OpenSSL
context = SSL.Context(SSL.TLSv1_2_METHOD)
context.use_privatekey_file('server.key')
context.use_certificate_file('server.crt')

# Создание нового цикла событий и выполнение асинхронной функции connect_to_server
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(connect_to_server(args.source))
