import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Вычисляем абсолютный путь до корня проекта (на уровень выше папки app)
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Указываем load_dotenv точный путь до файла .env
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# 3. Достаем ключ
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# 4. Защита от дурака (очень полезно при отладке!)
if not SECRET_KEY:
    raise ValueError("Секретный ключ не найден! Проверьте, что файл .env существует и заполнен.")