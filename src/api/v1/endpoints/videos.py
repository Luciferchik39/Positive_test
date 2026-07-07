"""# src/api/v1/endpoints/videos.py

POST /api/v1/videos/upload
    - Загрузка видео в MinIO
    - Создание записи в БД
    - Отправка задачи в Kafka

GET /api/v1/videos/{video_id}
    - Получение статуса обработки

GET /api/v1/videos/{video_id}/download
    - Скачивание обработанного видео"""