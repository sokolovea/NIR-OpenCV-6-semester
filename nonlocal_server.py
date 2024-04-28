import asyncio
import websockets

async def receive_from_server(websocket, path):
    while True:
        try:
            # Подключение к серверу на порту 9998
            async with websockets.connect('ws://localhost:9998') as server_websocket:
                while True:
                    try:
                        # Получение данных от сервера на порту 9998
                        data = await server_websocket.recv()
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

async def main(websocket, path):
    await receive_from_server(websocket, path)

start_server = websockets.serve(main, "localhost", 9999)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
