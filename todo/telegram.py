import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


class TelegramSendError(Exception):
    pass


def send_telegram_message(chat_id, text):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise TelegramSendError('Telegram bot token is not configured.')

    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = urllib.parse.urlencode(
        {
            'chat_id': chat_id,
            'text': text,
            'disable_web_page_preview': 'true',
        }
    ).encode()
    request = urllib.request.Request(url, data=payload, method='POST')

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise TelegramSendError('Telegram message could not be sent.') from exc

    if not data.get('ok'):
        raise TelegramSendError(data.get('description', 'Telegram API returned an error.'))

    return data
