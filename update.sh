#!/bin/bash
echo "Остановка мониторинга..."
sudo systemctl stop web-monitor.service

echo "Обновление кода..."
git pull

echo "Переустановка зависимостей..."
cd app
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate
cd ..

echo "Перезапуск мониторинга..."
sudo systemctl start web-monitor.service

echo "Обновление завершено!"