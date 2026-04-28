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
