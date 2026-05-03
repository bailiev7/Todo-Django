import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'К выполнению'
        IN_PROGRESS = 'in_progress', 'В процессе'
        DONE = 'done', 'Сделано'
        ARCHIVED = 'archived', 'В архиве'

    class Priority(models.IntegerChoices):
        LOW = 1, 'Низкий'
        MEDIUM = 2, 'Средний'
        HIGH = 3, 'Высокий'
        URGENT = 4, 'Срочный'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', '-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'priority']),
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=''),
                name='task_title_not_empty',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def clean(self):
        super().clean()

        if self.title:
            self.title = self.title.strip()

        if not self.title:
            raise ValidationError({'title': 'Титул задачи не может быть пустым.'})

        if self.completed_at and self.status != self.Status.DONE:
            raise ValidationError(
                {'completed_at': 'Время завершения можно установить только для завершенных задач.'}
            )

    def save(self, *args, **kwargs):
        if self.status == self.Status.DONE and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.status != self.Status.DONE:
            self.completed_at = None

        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status != self.Status.DONE
            and self.due_date < timezone.localdate()
        )


class TelegramAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_account',
    )
    chat_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Telegram аккаунт'
        verbose_name_plural = 'Telegram аккаунты'

    def __str__(self):
        username = f'@{self.username}' if self.username else self.chat_id
        return f'{self.user.get_username()} -> {username}'


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_link_tokens',
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Токен привязки Telegram'
        verbose_name_plural = 'Токены привязки Telegram'

    def __str__(self):
        return f'Telegram link token for {self.user.get_username()}'

    @property
    def is_active(self):
        return self.used_at is None and self.expires_at > timezone.now()


class Donation(models.Model):
    class Status(models.TextChoices):
        CREATED = 'created', 'Создан'
        PENDING = 'pending', 'Ожидает оплаты'
        SUCCEEDED = 'succeeded', 'Оплачен'
        CANCELED = 'canceled', 'Отменен'

    class PaymentMethod(models.TextChoices):
        ANY = 'any', 'Все доступные способы'
        BANK_CARD = 'bank_card', 'Банковская карта'
        SBP = 'sbp', 'СБП'
        YOO_MONEY = 'yoo_money', 'ЮMoney'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='donations',
        null=True,
        blank=True,
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1)],
    )
    currency = models.CharField(max_length=3, default='RUB')
    donor_name = models.CharField(max_length=120, blank=True)
    donor_email = models.EmailField(blank=True)
    message = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=24,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ANY,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )
    provider = models.CharField(max_length=32, default='yookassa')
    provider_payment_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    idempotence_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    confirmation_url = models.URLField(blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='todo_don_status_created_idx'),
            models.Index(fields=['provider_payment_id'], name='todo_don_payment_id_idx'),
            models.Index(fields=['public_id'], name='todo_don_public_id_idx'),
        ]
        verbose_name = 'Донат'
        verbose_name_plural = 'Донаты'

    def __str__(self):
        return f'Донат {self.amount} {self.currency} ({self.get_status_display()})'

    @property
    def is_paid(self):
        return self.status == self.Status.SUCCEEDED
