import cv2
import asyncio
import websockets
import base64

async def video_stream(websocket, path):
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Преобразование кадра в строку base64
        encoded_frame = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')
        
        # Отправка кадра серверу
        await websocket.send(encoded_frame)

start_server = websockets.serve(video_stream, "localhost", 9999)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
