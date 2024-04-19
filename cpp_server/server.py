import asyncio
import websockets

async def forward_frames(websocket, path, forward_host, forward_port):
    # Установка соединения с сервером для пересылки кадров
    forward_uri = f"ws://{forward_host}:{forward_port}"
    forward_connection = await websockets.connect(forward_uri)

    try:
        while True:
            # Получение кадра от клиента
            encoded_frame = await websocket.recv()

            # Пересылка кадра на сервер
            await forward_connection.send(encoded_frame)
    finally:
        # Закрытие соединения с сервером для пересылки кадров
        await forward_connection.close()

async def main():
    # Настройки сервера для принятия кадров от клиента
    server_host = "localhost"
    server_port = 9998

    # Настройки сервера для пересылки кадров
    forward_host = "localhost"
    forward_port = 9999

    # Запуск сервера для принятия кадров от клиента
    server = await websockets.serve(
        lambda websocket, path: forward_frames(websocket, path, forward_host, forward_port),
        server_host, server_port)

    # Ожидание завершения сервера
    await server.wait_closed()

# Запуск основной функции асинхронного сервера
asyncio.run(main())
