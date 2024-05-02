import asyncio
import websockets
from cryptography.fernet import Fernet
import cv2
import base64
import numpy as np
import torch
import torchvision
from imageai.Detection import ObjectDetection
import os
import sys

import datetime
from ultralytics import YOLO
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort

import json


# define some constants
CONFIDENCE_THRESHOLD = 0.8
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


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


# detector = ObjectDetection()
# detector.setModelTypeAsTinyYOLOv3()
# detector.setModelPath("yolov7-tiny.pt")
# detector.loadModel();

# load the pre-trained YOLOv8n model
model = YOLO("yolov8n.pt")
tracker = DeepSort(max_age=50)

def frame_neuro_processing(frame):
    start = datetime.datetime.now()
    detections = model(frame)[0]
    # loop over the detections
    for data in detections.boxes.data.tolist():
        # extract the confidence (i.e., probability) associated with the detection
        confidence = data[4]

        # filter out weak detections by ensuring the 
        # confidence is greater than the minimum confidence
        if float(confidence) < CONFIDENCE_THRESHOLD:
            continue

        # if the confidence is greater than the minimum confidence,
        # draw the bounding box on the frame
        xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])
        cv2.rectangle(frame, (xmin, ymin) , (xmax, ymax), GREEN, 2)
        
    #         ######################################
    # # TRACKING
    # ######################################
    # results = []
    # # update the tracker with the new detections
    # tracks = tracker.update_tracks(results, frame=frame)
    # # loop over the tracks
    # for track in tracks:
    #     # if the track is not confirmed, ignore it
    #     if not track.is_confirmed():
    #         continue

    #     # get the track id and the bounding box
    #     track_id = track.track_id
    #     ltrb = track.to_ltrb()

    #     xmin, ymin, xmax, ymax = int(ltrb[0]), int(
    #         ltrb[1]), int(ltrb[2]), int(ltrb[3])
    #     # draw the bounding box and the track id
    #     cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), GREEN, 2)
    #     cv2.rectangle(frame, (xmin, ymin - 20), (xmin + 20, ymin), GREEN, -1)
    #     cv2.putText(frame, str(track_id), (xmin + 5, ymin - 8),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 2)

    # # end time to compute the fps
    # end = datetime.datetime.now()
    # # show the time it took to process 1 frame
    # print(f"Time to process 1 frame: {(end - start).total_seconds() * 1000:.0f} milliseconds")
    # # calculate the frame per second and draw it on the frame
    # fps = f"FPS: {1 / (end - start).total_seconds():.2f}"
    # cv2.putText(frame, fps, (50, 50),
    #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 8)
    return frame

def frame_processing(frame):
    # Копирование исходного кадра для отрисовки
    frame_out = frame.copy()
    # Преобразование изображения в оттенки серого
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Вычитание фона
    fg_mask = backSub.apply(frame)
    # Устанавливаем глобальный порог для удаления теней
    retval, mask_thresh = cv2.threshold(fg_mask, 190, 255, cv2.THRESH_BINARY)
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
    cropped_images = []
    # Отрисовка прямоугольников вокруг больших контуров
    for cnt in large_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cropped_images.append(frame_out[y:y+h, x:x+w])
        # detections = model(frame_out[y:y+h, x:x+w])
        # detection = detections[0]

        # print("DETECTIONS = ", detections.box, "\n---")
        # class_id = int(detections[0])
        # confidence = detections[1]
        # label = f"{model.names[class_id]}: {confidence:.2f}"  # Составляем строку с меткой класса и уверенностью
        frame_out = cv2.rectangle(frame_out, (x, y), (x+w, y+h), (0, 0, 200), 3)
        # Отображаем прямоугольник и подписываем его меткой класса

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

                        instructions = await websocket.recv()
                        if instructions:
                            print("Получены инструкции:", instructions)
                            # Попытка парсинга JSON
                            try:
                                parsed_instructions = json.loads(instructions)
                                print("Распарсированные инструкции:", parsed_instructions)
                                # Далее вы можете обрабатывать распарсированные данные
                                # Например, выполнить какие-то действия на основе полученных инструкций
                            except json.JSONDecodeError:
                                print("Ошибка при парсинге JSON.")
                        else:
                            print("Пустой ответ от клиента.")

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
