# yandex_homework_bot

Telegramm-bot для уведомлений об изменении статуса домашних работ курса Backend-разработчик Яндекс.Практикума

### Версия языка

Проект создан на python 3.9.1

### Локальная установка и запуск

Склонировать проект в рабочую папку из репозитария:
``` 
git clone https://github.com/Andrey-Kolchugin/yandex_homework_bot.git
``` 
Перейти в папку проекта
```
сd homework_bot
```
Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Создать в директории проекта файл .env и внести туда данные для работы:
```python
PRACTICUM_TOKEN=<Ваш_токен_на_практикуме>
TELEGRAM_TOKEN=<id_бота>:<Токен_тг_бота>
TELEGRAM_CHAT_ID=<id_вашего_тг_чата>
```
Запустить проект:
```
python homework.py
```
