# Todo Home List 📝

Минималистичный веб-менеджер задач с полной поддержкой аутентификации, интеграцией Telegram-бота для восстановления пароля, системой донатов и GDPR-совместимым баннером cookies.

![Django](https://img.shields.io/badge/Django-6.0-green?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-orange?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square)

---

## 🎯 Основные возможности

### Управление задачами
- ✅ Создание, редактирование и удаление задач
- 📊 Фильтрация по статусу (новая, в процессе, сделано, архив)
- 🎯 Установка приоритета (низкий, средний, высокий, срочный)
- 📅 Установка сроков выполнения с визуальным отображением просроченных задач
- 🔄 Быстрое переключение статуса задачи

### Аутентификация и безопасность
- 🔐 Регистрация и авторизация пользователей
- 🔑 Восстановление пароля через email
- 🤖 **Альтернативное восстановление через Telegram-бота**
- 📱 Привязка Telegram аккаунта в настройках профиля
- 🛡️ CSRF защита, защита от SQL injection и XSS

### Интеграции
- 💬 **Telegram Bot API** — отправка ссылок для сброса пароля
- 💳 **YooKassa** — система приёма донатов
- 📧 Email для уведомлений
- 🍪 **Cookie Consent** — GDPR-совместимый баннер

### Дизайн и UX
- 📱 Полностью адаптивный интерфейс
- 🎨 Современная UI с анимациями
- ⚡ Оптимизированная производительность
- 🌙 Чистый минималистичный дизайн

---

## 🛠️ Технологический стек

### Backend
- **Django 6.0** — современный веб-фреймворк
- **PostgreSQL 14+** — надёжная база данных
- **Python 3.10+** — язык разработки
- **Gunicorn** — WSGI приложение сервер
- **Nginx** — обратный прокси

### Frontend
- **HTML5 / CSS3** — семантичная разметка и современные стили
- **JavaScript (Vanilla)** — интерактивность без фреймворков
- **AJAX** — асинхронные операции

### DevOps & Deployment
- **Docker & Docker Compose** — контейнеризация
- **GNU Make** — автоматизация команд

---

## 🚀 Быстрый старт с Docker

### Требования
- Docker и Docker Compose
- Git

### Установка

1. **Клонирование репозитория**
```bash
git clone https://github.com/yourusername/todo-home-list.git
cd todo-home-list
```

2. **Копирование файла конфигурации**
```bash
cp .env.example .env
```

3. **Запуск проекта**
```bash
docker compose up --build
```

4. **Доступ к приложению**
```
http://localhost:8000       # Production сервер (Nginx)
http://localhost:8001       # Development сервер Django (если включен)
```

---

## ⚙️ Конфигурация

### Основные переменные окружения (.env)

```env
# === Django Configuration ===
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DJANGO_LANGUAGE_CODE=ru-ru
DJANGO_TIME_ZONE=Europe/Moscow

# === Database (PostgreSQL) ===
POSTGRES_DB=mysite
POSTGRES_USER=mysite
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# === Email Settings ===
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=smtp.gmail.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=your-email@gmail.com
DJANGO_EMAIL_HOST_PASSWORD=your-app-password
DJANGO_EMAIL_USE_TLS=True

# === Telegram Bot ===
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_WEBHOOK_SECRET=your-random-secret-string

# === YooKassa (Payments) ===
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=your-secret-key
DONATION_FAKE_GATEWAY=False
DONATION_CURRENCY=RUB
DONATION_MIN_AMOUNT=50.00
DONATION_MAX_AMOUNT=100000.00
```

### Настройка Telegram Bot

1. **Создание бота через @BotFather**
```bash
# Отправьте команду /newbot боту @BotFather
# Получите токен в формате: 123456:ABC-DEF...
```

2. **Установка webhook**
```bash
curl -X POST https://api.telegram.org/bot{TOKEN}/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://yourdomain.com/telegram/webhook/",
    "secret_token": "your-random-secret-string"
  }'
```

3. **Проверка статуса**
```bash
curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo
```

### Настройка YooKassa

1. Зарегистрируйтесь на [YooKassa](https://yookassa.ru)
2. Получите Shop ID и Secret Key
3. Настройте webhook для событий:
   - `payment.succeeded`
   - `payment.canceled`
4. Установите переменные в `.env`

---

## 📖 Использование

### Для пользователей

1. **Создание аккаунта**
   - Перейдите на главную страницу
   - Кликните "Создать аккаунт"
   - Укажите имя пользователя и пароль

2. **Управление задачами**
   - Добавляйте новые задачи в левую панель
   - Устанавливайте статус, приоритет и сроки
   - Переключайте статус прямо из списка
   - Архивируйте или удаляйте ненужные задачи

3. **Привязка Telegram**
   - Перейдите в "Настройки"
   - Кликните "Привязать Telegram"
   - Следуйте инструкциям бота

4. **Восстановление пароля**
   - Выберите способ восстановления (email или Telegram)
   - Укажите имя пользователя или email
   - Получите ссылку для сброса

### Для администраторов

#### Полезные команды

```bash
# Миграции базы данных
make migrate

# Создание суперпользователя
make superuser

# Запуск тестов
make test

# Сбор статических файлов
make collectstatic

# Django shell для отладки
make shell
```

#### Или напрямую через Docker

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
docker compose exec web python manage.py shell
```

#### Доступ к админ-панели
```
http://localhost:8000/admin
```

Используйте учётные данные суперпользователя для входа.

---

## 📁 Структура проекта

```
mysite/
├── mysite/                      # Конфиг проекта
│   ├── settings.py              # Основные настройки
│   ├── urls.py                  # Маршруты на уровне проекта
│   ├── wsgi.py                  # WSGI для Gunicorn
│   └── asgi.py                  # ASGI конфиг
├── todo/                        # Основное приложение
│   ├── models.py                # Модели БД (Task, User, TelegramAccount, Donation)
│   ├── views.py                 # Обработчики запросов и логика
│   ├── forms.py                 # Django формы и валидация
│   ├── urls.py                  # Маршруты приложения
│   ├── telegram.py              # Интеграция с Telegram API
│   ├── payments.py              # Интеграция с YooKassa
│   ├── admin.py                 # Админ-панель
│   └── migrations/              # Миграции БД
├── templates/                   # HTML шаблоны
│   ├── todo/                    # Шаблоны приложения todo
│   ├── registration/            # Шаблоны аутентификации
│   └── Privacy-terms/           # Юридические документы
├── static/                      # Статические файлы
│   ├── css/                     # Стили (dashboard, home, cookies)
│   └── js/                      # JavaScript (логика и анимации)
├── docker-compose.yml           # Docker Compose конфиг
├── Dockerfile                   # Docker образ
├── Makefile                     # Команды автоматизации
├── manage.py                    # Django управление
├── requirements.txt             # Python зависимости
└── README.md                    # Этот файл
```

---

## 🌐 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|---------|
| GET | `/` | Главная страница с аутентификацией |
| POST | `/accounts/register/` | Регистрация нового пользователя |
| POST | `/accounts/login/` | Авторизация пользователя |
| GET | `/accounts/logout/` | Выход из аккаунта |
| GET | `/tasks/` | Список задач пользователя с фильтрацией |
| POST | `/tasks/create/` | Создание новой задачи |
| POST | `/tasks/<id>/update/` | Обновление задачи |
| POST | `/tasks/<id>/delete/` | Удаление задачи |
| GET | `/accounts/settings/` | Настройки профиля |
| GET | `/accounts/password/reset/` | Форма восстановления (email) |
| POST | `/telegram/password-reset/` | Восстановление через Telegram |
| GET | `/telegram/link/` | Привязка Telegram аккаунта |
| POST | `/telegram/webhook/` | Webhook от Telegram бота |
| GET | `/donate/` | Страница донатов |
| POST | `/donate/webhook/` | Webhook от YooKassa |

---

## 🔒 Безопасность

### Встроенные механизмы защиты

- ✅ **CSRF Protection** — Django CSRF токены на всех POST запросах
- ✅ **SQL Injection Protection** — использование Django ORM
- ✅ **XSS Protection** — автоматическое экранирование шаблонов
- ✅ **Password Security** — bcrypt хеширование через Django
- ✅ **Secure Sessions** — httpOnly cookies
- ✅ **Input Validation** — валидация на уровне формы и модели
- ✅ **HTTPS Support** — готовность к SSL/TLS
- ✅ **CORS Configuration** — настройка в settings.py

### Рекомендации для production

```env
# Отключите debug режим
DJANGO_DEBUG=False

# Установите правильные хосты
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Используйте защищённые cookies
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=True

# Включите HSTS
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
make test

# Или напрямую
docker compose exec web python manage.py test

# С покрытием (если установлен coverage)
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
```

---

## 🐛 Решение проблем

### Telegram бот не отправляет сообщения

**Причины и решения:**
1. Проверьте переменные окружения `TELEGRAM_BOT_TOKEN` и `TELEGRAM_WEBHOOK_SECRET`
2. Убедитесь, что пользователь привязал Telegram в настройках
3. Проверьте логи: `docker compose logs web`
4. Тестируйте в Django shell:
   ```bash
   make shell
   from todo.telegram import send_telegram_message
   send_telegram_message(chat_id, "Test message")
   ```

### Платежи YooKassa не работают

**Проверьте:**
1. В тестовом режиме: `DONATION_FAKE_GATEWAY=True`
2. В production: наличие Shop ID и Secret Key
3. Webhook URL доступен извне (https только)
4. Логи: `docker compose logs web | grep -i yookassa`

### Миграции не применяются

```bash
# Если миграции konflictуют
docker compose exec web python manage.py migrate --fake-initial

# Или создайте новую миграцию
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### База данных не подключается

```bash
# Проверьте переменные .env
# Перезагрузите контейнеры
docker compose down
docker compose up --build

# Или вручную создайте БД
docker compose exec db psql -U mysite -c "CREATE DATABASE mysite;"
```

---

## 🤝 Способы помощи проекту

### Финансовая поддержка
- 💳 [Отправьте донат](http://localhost:8000/donate/)

### Техническая помощь
1. Найдите issue или создайте новый
2. Сделайте fork репозитория
3. Создайте ветку для функции: `git checkout -b feature/amazing-feature`
4. Commit изменения: `git commit -m 'Add amazing feature'`
5. Push в ветку: `git push origin feature/amazing-feature`
6. Откройте Pull Request

### Чек-лист перед PR
- ✅ Код следует стилю проекта
- ✅ Добавлены или обновлены тесты
- ✅ Документация обновлена
- ✅ Нет console.log или debug кода
- ✅ Миграции применяются без ошибок

---

## 📜 Лицензия

Проект распространяется под лицензией MIT. Подробнее см. [LICENSE](LICENSE).

---

## 📞 Контакты и поддержка

| Канал | Ссылка |
|-------|--------|
| 💬 Telegram | [@bailiev](https://t.me/bailiev) |
| 📧 Email | a.baylyyew05@gmail.com |
| 𝕏 Twitter | [@bailiev_7](https://x.com/bailiev_7) |

---

## 📊 Статистика проекта

- 📝 Модели: 5 (Task, User, TelegramAccount, TelegramLinkToken, Donation)
- 📄 Шаблонов: 15+
- 🎨 CSS файлов: 8+
- 🔧 JavaScript модулей: 5+
- ✅ Endpoints: 18+

---

## 🙏 Благодарности

- [Django](https://www.djangoproject.com/) — отличный веб-фреймворк
- [PostgreSQL](https://www.postgresql.org/) — надёжная база данных
- [Telegram Bot API](https://core.telegram.org/bots/api) — простая интеграция
- [YooKassa](https://yookassa.ru/) — платёжная система
- Все контрибьюторы и пользователи! ❤️

---

**Сделано с ❤️ на Django**

*Последнее обновление: Май 2026*
