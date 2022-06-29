import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram.ext
from dotenv import load_dotenv
from telegram import Bot
import exceptions

load_dotenv()


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

ANSWER_ERROR = 'Получен неккоректный ответ'


def send_message(bot, message):
    """Отправляет подготовленное сообщение в ТГ."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Попытка отправить сообщение')
    except Exception as error:
        raise exceptions.SendMessageError(
            'Не удалось отправить сообщение'
        ) from error
    else:
        logger.debug('Сообщение успешно отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к домашке и получает api ответю."""
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.debug('Выполняем запрос к API')
    except Exception as error:
        if response.status_code != HTTPStatus.OK:
            raise ConnectionError(
                f'Ошибка коннекта к эндпоинту {ENDPOINT}'
                f'загововок={HEADERS} params={params}'
            ) from error
    else:
        return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    logger.debug('Начинаем прверку ответа на соответствие API')
    if not isinstance(response, dict):
        raise TypeError('Ошибка ответа, тип объекта !=dict')
    try:
        homework = response['homeworks']
    except KeyError as error:
        raise KeyError('В ответе отсутствует ключ homeworks') from error
    if response.get('current_date') is None:
        raise KeyError('В ответе отсутствует ключ current_date')
    if not homework:
        raise KeyError('Отсутствует список домашек')
    if len(homework) == 0:
        raise exceptions.EmptyWorkListError('Задания на ревью не отправлялись')
    if not isinstance(homework, list):
        raise TypeError('Ошибка формата вывода домашек')
    return homework


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise exceptions.StatusKeyError('Не найден ключ homework_name')
    homework_status = homework.get('status')
    if homework_status is None:
        raise exceptions.StatusKeyError('Не найден ключ status')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        raise exceptions.StatusKeyError(
            'Отсутствует сообщение о статусе проверки'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all(PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


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
    main()
