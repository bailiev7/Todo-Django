# Todo Home List

Django project with a todo dashboard, user accounts, and password reset flow.

## Stack

- Python 3.12
- Django
- PostgreSQL
- Gunicorn
- Nginx
- Docker Compose

## Local Start

1. Create an environment file:

```bash
cp .env.example .env
```

2. Update values in `.env` if needed.

3. Start the project:

```bash
docker compose up --build
```

4. Open:

```text
http://localhost:8000
```

With `docker-compose.override.yml`, Django also exposes the development server on:

```text
http://localhost:8001
```

## Useful Commands

```bash
make migrate
make superuser
make test
make collectstatic
```

Or run commands directly:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

## Email

Password reset uses Django email settings from `.env`.

For local development, keep:

```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

For production, use a real SMTP provider and a verified sender domain.

## Donations

The donation flow uses YooKassa Redirect payments:

1. Django creates a local `Donation`.
2. Django creates a YooKassa payment with a unique idempotence key.
3. The user is redirected to YooKassa and chooses a payment method.
4. YooKassa returns the user to `/donate/return/<public_id>/`.
5. Django verifies the payment status with YooKassa and shows the result.
6. `/donate/webhook/` accepts YooKassa notifications and updates the local status.

Required production settings:

```env
DONATION_FAKE_GATEWAY=False
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
```

For local learning without a YooKassa test shop, keep:

```env
DONATION_FAKE_GATEWAY=True
```

In this mode the app creates a local mock payment, redirects through the same return page, marks the donation as paid, and never calls YooKassa.

In the YooKassa dashboard, subscribe the public webhook URL to:

```text
payment.succeeded
payment.canceled
```

For fiscal receipts, enable `YOOKASSA_SEND_RECEIPT=True` only after confirming the correct VAT and payment subject values for your business model.
