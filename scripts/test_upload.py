# scripts/test_upload.py
import time

import requests


# Загрузка видео
def upload_video(file_path: str, title: str, description: str = ""):
    url = "http://localhost:8000/api/v1/videos/upload"

    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"title": title, "description": description}

        response = requests.post(url, files=files, data=data)
        print(f"Upload response: {response.json()}")
        return response.json()


# Получение статуса
def get_status(video_id: str):
    url = f"http://localhost:8000/api/v1/videos/{video_id}/status"
    response = requests.get(url)
    print(f"Status: {response.json()}")
    return response.json()


# Скачивание видео
def download_video(video_id: str, output_path: str):
    url = f"http://localhost:8000/api/v1/videos/{video_id}/download"
    response = requests.get(url, stream=True)

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Video downloaded to {output_path}")


if __name__ == "__main__":
    # Загружаем видео
    result = upload_video("test_video.mp4", "My Test Video", "Test upload")
    video_id = result["id"]

    # Проверяем статус
    time.sleep(2)
    get_status(video_id)

    # Скачиваем видео
    # download_video(video_id, "downloaded_video.mp4")
