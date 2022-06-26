import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram.ext
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    encoding='utf-8',
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

UNKNOWN_STATUS = 'Неизвестный статус работы {status}'

ANSWER_ERROR = 'Получен неккоректный ответ'

NEW_STATUS = 'Изменился статус проверки работы "{homework_name}". {verdict}'

API_KEYS = ('status', 'homework_name')


def send_message(bot, message):
    """Отправляет подготовленное сообщение в ТГ."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        log_message = 'удачная отправка сообщения в Telegram'
        logger.info(log_message)
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение {error}', exc_info=True)
        raise ConnectionError(error)


def get_api_answer(current_timestamp):
    """Делает запрос к домашке и получает api ответю."""
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            log_message = 'Эндпоинт недоступен'
            logger.error(log_message)
            raise ConnectionError
        return response.json()
    except Exception as error:
        print(error)
        raise ConnectionError(ANSWER_ERROR)


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homework = response['homeworks']
    except KeyError as error:
        log_message = f'Отсутствует ключ homeworks {error}'
        logger.error(log_message)
        raise KeyError(log_message)
    if not homework:
        log_message = 'Отсутствует спикок домашек'
        logger.error(log_message)
        raise KeyError(log_message)
    if len(homework) == 0:
        log_message = 'Задания на ревью не отправлялись'
        logger.error(log_message)
        raise ValueError(log_message)
    if not isinstance(homework, list):
        log_message = 'Ошибка формата вывода домашек'
        logger.error(log_message)
        raise TypeError(log_message)
    return homework


def parse_status(homework):
    """Извлекает статус домашней работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        log_message = f'Не найден ключ homework_name {error}'
        logger.error(log_message)
        raise KeyError(log_message)
    try:
        homework_status = homework['status']
    except KeyError as error:
        log_message = f'Не найден ключ status {error}'
        logger.error(log_message)
        raise KeyError(log_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        log_message = 'Отсутствует сообщение о статусе проверки'
        logger.error(log_message)
        raise KeyError(log_message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID) is None:
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - RETRY_TIME
    while True:
        try:
            if not check_tokens():
                log_message = 'Нет необходимых токенов!'
                logger.critical(log_message)
                raise SystemExit(log_message)
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            send_message(bot, message)
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)
        except Exception as error:
            log_message = f'Сбой в работе программы: {error}'
            logger.error(log_message)
            send_message(bot, f'{log_message} {error}')
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
