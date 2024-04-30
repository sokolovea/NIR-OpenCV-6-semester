import cv2
import asyncio
import websockets
import base64
import argparse
import numpy as np
from cryptography.fernet import Fernet

async def video_stream(websocket, video_source, key):
    '''
    Трансляция видеопотока другому серверу
    '''
    cipher_suite = Fernet(key)
    cap = cv2.VideoCapture(video_source)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Преобразование кадра в строку base64
        frame = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8') 
               
        # Шифруем строку
        encoded_frame = cipher_suite.encrypt(frame.encode())

        try:
            if websocket.open:
                await websocket.send(encoded_frame)
            else:
                print("Клиент отключился. Прекращение отправки данных.")
                break
        except websockets.exceptions.ConnectionClosedError:
            print("Соединение с клиентом закрыто. Прекращение отправки данных.")
            break

# Обработка аргументов командной строки для определения источника видео
parser = argparse.ArgumentParser(description='Отправка видео')
parser.add_argument('--source', default=0, help='Источник видео (0 - веб-камера, иначе имя файла)')
args = parser.parse_args()

# Запуск сервера
key = b'2na2SazDd926u9bR5Sn5MBJBsuIsyANgdKERwhyBmag='
start_server = websockets.serve(lambda websocket: video_stream(websocket, args.source, key), "localhost", 9998)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()