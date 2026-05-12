from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from todo.telegram import send_telegram_message, TelegramSendError
from todo.payments import get_payment_client

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_telegram_message_task(self, chat_id, text):
    """
    Асинхронная отправка сообщения в Telegram.

    Args:
        chat_id: ID чата в Telegram
        text: Текст сообщения

    Returns:
        dict: Результат отправки сообщения
    """
    try:
        result = send_telegram_message(chat_id, text)
        return {
            'status': 'success',
            'message': f'Сообщение отправлено чату {chat_id}',
            'data': result
        }
    except TelegramSendError as exc:
        # Повторить попытку через 5 секунд (max 3 попытки)
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=2)
def send_email_task(self, recipient_email, subject, message, from_email=None):
    """
    Асинхронная отправка email письма.

    Args:
        recipient_email: Email адрес получателя
        subject: Тема письма
        message: Текст письма
        from_email: Email отправителя (опционально)

    Returns:
        dict: Результат отправки
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return {
            'status': 'success',
            'message': f'Email отправлен на {recipient_email}'
        }
    except Exception as exc:
        # Повторить через 10 секунд (max 2 попытки)
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True)
def create_yookassa_payment_task(self, donation_id, return_url):
    """
    Асинхронное создание платежа в YooKassa.

    Args:
        donation_id: ID пожертвования
        return_url: URL для возврата после платежа

    Returns:
        dict: Данные платежа
    """
    from todo.models import Donation

    try:
        donation = Donation.objects.get(pk=donation_id)
        payment_client = get_payment_client()

        payment = payment_client.create_payment(donation, return_url)
        return {
            'status': 'success',
            'payment_id': payment.get('id'),
            'confirmation_url': payment.get('confirmation', {}).get('confirmation_url')
        }
    except Exception as exc:
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def verify_yookassa_payment_task(donation_id, payment_id):
    """
    Асинхронная проверка статуса платежа в YooKassa.

    Args:
        donation_id: ID пожертвования
        payment_id: ID платежа в YooKassa

    Returns:
        dict: Статус платежа
    """
    from todo.models import Donation

    try:
        donation = Donation.objects.get(pk=donation_id)
        payment_client = get_payment_client()

        payment = payment_client.get_payment(payment_id)
        return {
            'status': 'success',
            'paid': payment.get('paid', False),
            'payment_status': payment.get('status')
        }
    except Exception as exc:
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def cleanup_expired_telegram_tokens():
    """
    Периодическая очистка истёкших токенов привязки Telegram.
    Рекомендуется запускать раз в час.
    """
    from django.utils import timezone
    from datetime import timedelta
    from todo.models import TelegramLinkToken

    cutoff_time = timezone.now() - timedelta(hours=1)
    deleted_count, _ = TelegramLinkToken.objects.filter(
        created_at__lt=cutoff_time
    ).delete()

    return {
        'status': 'success',
        'deleted_tokens': deleted_count
    }
