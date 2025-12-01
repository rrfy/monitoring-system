#!/usr/bin/env python3
"""
Мониторинг простого веб-приложения с автоматическим перезапуском при сбоях.
Проверяет, что сервер отвечает любым 2xx-кодом и содержит строку "Hello World".
"""

import time
import requests
import logging
import subprocess
import yaml
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Путь к текущей директории скрипта
BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = BASE_DIR / "log"
LOG_FILE = LOG_DIR / "monitor.log"

# Создаём папку для логов
LOG_DIR.mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
#        logging.StreamHandler(sys.stdout)  можно дополнительно дополнительно вывести в консоль
    ]
)

def load_config():
    """Загружает конфигурацию из config.yaml"""
    config_path = BASE_DIR / "config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Не удалось загрузить конфиг {config_path}: {e}")
        sys.exit(1)

def is_success_response(response: requests.Response) -> bool:
    """
    Проверяет, что ответ успешный:
    - статус-код из 200-х ответов
    - в теле ответа есть строка "Hello World" (без учёта регистра и пробелов)
    """
    if not response.status_code // 100 == 2:
        logging.debug(f"Получен не-2xx код: {response.status_code}")
        return False

    try:
        text = response.text.strip()
        if "hello world" not in text.lower():
            logging.debug("В ответе нет строки 'Hello World'")
            return False
    except Exception:
        logging.debug("Не удалось прочитать тело ответа")
        return False

    return True

def check_app(url: str, timeout: int) -> bool:
    """Выполняет проверку доступности приложения"""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        logging.info(f"Проверка {url} → {response.status_code}")
        return is_success_response(response)
    except requests.RequestException as e:
        logging.warning(f"Ошибка при запросе к {url}: {e}")
        return False

def terminate_process_tree(pid: int):
    """Убивает процесс и всех его детей"""
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        logging.info(f"Процесс {pid} (и его дети) завершён")
    except ProcessLookupError:
        pass
    except Exception as e:
        logging.warning(f"Не удалось убить процесс {pid}: {e}")

def start_app():
    """Запускает веб-приложение в отдельном процессе"""
    logging.info("Запуск веб-приложения...")
    # Запускаем в отдельной процесс-группе, чтобы потом можно было убить всех потомков
    process = subprocess.Popen(
        ["python3", "../app/app.py"],
        cwd=BASE_DIR / ".." / "app",
        preexec_fn=os.setsid  # важная строчка для корректного kill'а детей
    )
    logging.info(f"Приложение запущено с PID {process.pid}")
    return process.pid

def main():
    config = load_config()

    url = config.get("app_url", "http://127.0.0.1:5000")
    interval = config.get("check_interval", 10)
    timeout = config.get("timeout", 5)

    logging.info("Система мониторинга запущена")
    logging.info(f"URL: {url} | Интервал: {interval}с | Таймаут: {timeout}с")

    current_pid = None

    while True:
        if not check_app(url, timeout):
            logging.warning(f"Приложение недоступно! Перезапуск...")

            # Убиваем старый процесс, если он есть
            if current_pid:
                terminate_process_tree(current_pid)

            time.sleep(2)  # небольшая пауза перед новым запуском
            current_pid = start_app()
        else:
            logging.info("Приложение работает корректно")

        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Мониторинг остановлен пользователем")
    except Exception as e:
        logging.exception(f"Критическая ошибка: {e}")