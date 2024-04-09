import time

import httpx
import os

# Отправка запроса на fast api
async def send_request(selected_question, user_input):
    # URL FastAPI-сервера
    fast_api_url = os.getenv('ADDRESS')

    data = {"data": {"Question": selected_question, "Text": user_input}}

    start_time = time.time()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(fast_api_url, json=data)

    end_time = time.time()

    # Вывод времени запроса
    duration = end_time - start_time

    # Вывод error'a в случаи неуспеха
    if response.status_code == 200:
        return response.json(), duration
    else:
        return {
            "error": f"HTTP Error {response.status_code}: {response.text}"
        }, duration