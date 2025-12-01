#!/bin/bash
set -e

echo "Установка зависимостей приложения..."
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "Создание директорий и прав..."
mkdir -p monitor/log
chmod +x monitor/monitor.py
chmod +x start_monitoring.sh
chmod +x update.sh

echo "Установка systemd-сервиса..."
sudo cp systemd/web-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable web-monitor.service

echo "Готово! Запустите мониторинг:
echo "   sudo systemctl start web-monitor.service"
echo "Или вручную: ./start_monitoring.sh"