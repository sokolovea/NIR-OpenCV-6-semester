import cv2
import asyncio
import websockets
import base64
import argparse
import os
import uuid
import time


async def video_stream(websocket, path, video_source):
    video_counter = 0
    cap = cv2.VideoCapture(video_source)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
       # Преобразование кадра в оттенки серого
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Выделение границ
        edges = cv2.Canny(gray, 50, 150)
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        combined_frame = cv2.addWeighted(frame, 0.8, edges_bgr, 1, 0)
        
        # Преобразование кадра в строку base64
        encoded_frame = base64.b64encode(cv2.imencode('.jpg', combined_frame)[1]).decode('utf-8')
    
        # Сохранение кадра в файл
        if (video_counter % 30 == 0):
            timestamp = str(time.time())
            file_name = os.path.join('test', timestamp + str(video_counter) + '.jpg')
            
            with open(file_name, 'wb') as f:
                f.write(cv2.imencode('.jpg', combined_frame)[1])
        video_counter += 1
        
        # Отправка кадра серверу
        await websocket.send(encoded_frame)


parser = argparse.ArgumentParser(description='Отправка видео')
parser.add_argument('--source', default=0, help='Источник видео (0 - веб-камера, иначе имя файла)')
args = parser.parse_args()

start_client = websockets.serve(lambda websocket, path: video_stream(websocket, path, args.source), "localhost", 9999)

asyncio.get_event_loop().run_until_complete(start_client)
asyncio.get_event_loop().run_forever()