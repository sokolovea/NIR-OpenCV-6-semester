import cv2
import asyncio
import websockets
import base64
import argparse
import os
import uuid
import time
import numpy as np

async def video_stream(websocket, path, video_source):
    video_counter = 0
    cap = cv2.VideoCapture(video_source)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # # Преобразование кадра в оттенки серого
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # # Выделение границ
        # edges = cv2.Canny(gray, 50, 150)
        # edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        # combined_frame = cv2.addWeighted(frame, 0.8, edges_bgr, 1, 0)
        
        # Преобразование кадра в строку base64
        encoded_frame = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')        

        try:
            # Проверка, что клиент все еще подключен
            if websocket.open:
                # Отправка кадра клиенту
                await websocket.send(encoded_frame)
            else:
                print("Клиент отключился. Прекращение отправки данных.")
                break
        except websockets.exceptions.ConnectionClosedError:
            print("Соединение с клиентом закрыто. Прекращение отправки данных.")
            break

parser = argparse.ArgumentParser(description='Отправка видео')
parser.add_argument('--source', default=0, help='Источник видео (0 - веб-камера, иначе имя файла)')
args = parser.parse_args()

start_server= websockets.serve(lambda websocket, path: video_stream(websocket, path, args.source), "localhost", 9998)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()