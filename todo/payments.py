import base64
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from todo.models import Donation


class PaymentGatewayError(Exception):
    pass


class FakeDonationGateway:
    provider = 'mock'
    is_fake = True

    @property
    def is_configured(self):
        return True

    def create_payment(self, donation, return_url):
        return {
            'id': f'mock_{donation.public_id}',
            'status': 'pending',
            'paid': False,
            'confirmation': {
                'type': 'redirect',
                'confirmation_url': self._with_query(return_url, {'mock_payment': 'paid'}),
            },
            'metadata': {
                'donation_id': str(donation.pk),
                'public_id': str(donation.public_id),
            },
        }

    def get_payment(self, payment_id):
        return {
            'id': payment_id,
            'status': 'succeeded',
            'paid': True,
            'test': True,
        }

    def _with_query(self, url, params):
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}{urlencode(params)}'


class YooKassaClient:
    provider = 'yookassa'
    is_fake = False

    def __init__(self):
        self.shop_id = settings.YOOKASSA_SHOP_ID
        self.secret_key = settings.YOOKASSA_SECRET_KEY
        self.api_url = settings.YOOKASSA_API_URL.rstrip('/')
        self.timeout = settings.YOOKASSA_TIMEOUT

    @property
    def is_configured(self):
        return bool(self.shop_id and self.secret_key)

    def create_payment(self, donation, return_url):
        payload = {
            'amount': {
                'value': self._money(donation.amount),
                'currency': donation.currency,
            },
            'capture': True,
            'confirmation': {
                'type': 'redirect',
                'return_url': return_url,
            },
            'description': f'Донат Todo Home List #{donation.pk}',
            'metadata': {
                'donation_id': str(donation.pk),
                'public_id': str(donation.public_id),
            },
            'save_payment_method': False,
        }

        if donation.payment_method != Donation.PaymentMethod.ANY:
            payload['payment_method_data'] = {'type': donation.payment_method}

        if settings.YOOKASSA_SEND_RECEIPT and donation.donor_email:
            payload['receipt'] = {
                'customer': {'email': donation.donor_email},
                'items': [
                    {
                        'description': 'Донат Todo Home List',
                        'quantity': '1.00',
                        'amount': payload['amount'],
                        'vat_code': settings.YOOKASSA_VAT_CODE,
                        'payment_mode': 'full_payment',
                        'payment_subject': settings.YOOKASSA_PAYMENT_SUBJECT,
                    }
                ],
            }

        return self._request(
            'POST',
            '/payments',
            payload=payload,
            idempotence_key=str(donation.idempotence_key),
        )

    def get_payment(self, payment_id):
        return self._request('GET', f'/payments/{payment_id}')

    def _request(self, method, path, payload=None, idempotence_key=None):
        if not self.is_configured:
            raise PaymentGatewayError('ЮKassa не настроена: нет shop_id или secret_key.')

        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        request = Request(
            f'{self.api_url}{path}',
            data=body,
            method=method,
            headers=self._headers(idempotence_key),
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = response.read().decode('utf-8')
        except HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise PaymentGatewayError(f'ЮKassa вернула HTTP {exc.code}: {detail}') from exc
        except URLError as exc:
            raise PaymentGatewayError(f'Не удалось соединиться с ЮKassa: {exc.reason}') from exc
        except TimeoutError as exc:
            raise PaymentGatewayError('ЮKassa не ответила за отведенное время.') from exc

        return json.loads(data) if data else {}

    def _headers(self, idempotence_key=None):
        credentials = f'{self.shop_id}:{self.secret_key}'.encode('utf-8')
        headers = {
            'Authorization': f'Basic {base64.b64encode(credentials).decode("ascii")}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TodoHomeList/1.0 Django',
        }

        if idempotence_key:
            headers['Idempotence-Key'] = idempotence_key

        return headers

    def _money(self, amount):
        return f'{Decimal(amount):.2f}'


def get_payment_client(provider=None):
    if provider == FakeDonationGateway.provider or settings.DONATION_FAKE_GATEWAY:
        return FakeDonationGateway()

    return YooKassaClient()
