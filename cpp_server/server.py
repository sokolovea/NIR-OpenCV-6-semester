import asyncio
import websockets

async def forward_data(data, target_port):
    async with websockets.connect(f"ws://localhost:{target_port}") as websocket:
        await websocket.send(data)
        response = await websocket.recv()
        return response

async def handle_client(websocket, path):
    target_port = 9999
    try:
        while True:
            # Получение данных от клиента
            data = await websocket.recv()

            # Пересылка данных на целевой порт
            try:
                response = await asyncio.wait_for(forward_data(data, target_port), timeout=5)
            except asyncio.TimeoutError:
                response = "Timeout occurred while forwarding data to the target port."

            # Отправка ответа клиенту
            await websocket.send(response)
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected")

start_server = websockets.serve(handle_client, "localhost", 9998)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()