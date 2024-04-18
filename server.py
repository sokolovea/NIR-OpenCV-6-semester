import cv2
import asyncio
import websockets
import base64
import argparse

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

parser = argparse.ArgumentParser(description='Video streaming client')
parser.add_argument('--source', default=0, help='Video source (0 for webcam, path to file for file)')
args = parser.parse_args()

start_client = websockets.serve(lambda websocket, path: video_stream(websocket, path, args.source), "localhost", 9999)

asyncio.get_event_loop().run_until_complete(start_client)
asyncio.get_event_loop().run_forever()