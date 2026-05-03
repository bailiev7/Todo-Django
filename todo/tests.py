import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from todo.forms import TaskForm, TodoSetPasswordForm
from todo.models import Donation, Task, TelegramAccount, TelegramLinkToken
from todo.views import token_hash


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='secret123',
        )

    def test_done_task_sets_completed_at(self):
        task = Task.objects.create(
            user=self.user,
            title='Finish report',
            status=Task.Status.DONE,
        )

        self.assertIsNotNone(task.completed_at)

    def test_non_done_task_clears_completed_at(self):
        task = Task.objects.create(
            user=self.user,
            title='Prepare sprint',
            status=Task.Status.DONE,
        )
        task.status = Task.Status.TODO
        task.save()

        self.assertIsNone(task.completed_at)

    def test_title_is_trimmed_and_cannot_be_blank(self):
        task = Task(user=self.user, title='   ')

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_is_overdue_returns_true_for_past_due_incomplete_task(self):
        task = Task.objects.create(
            user=self.user,
            title='Pay bills',
            due_date=timezone.localdate() - timezone.timedelta(days=1),
            status=Task.Status.IN_PROGRESS,
        )

        self.assertTrue(task.is_overdue)


class TaskFormTests(TestCase):
    def test_due_date_cannot_be_in_the_past(self):
        form = TaskForm(
            data={
                'title': 'Write summary',
                'description': '',
                'status': Task.Status.TODO,
                'priority': Task.Priority.MEDIUM,
                'due_date': timezone.localdate() - timezone.timedelta(days=1),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_due_date_input_min_is_today(self):
        form = TaskForm()

        self.assertEqual(
            form.fields['due_date'].widget.attrs['min'],
            timezone.localdate().isoformat(),
        )


class TaskDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboard-user',
            password='secret123',
        )
        TelegramAccount.objects.create(user=self.user, chat_id='987654321')
        self.client.login(username='dashboard-user', password='secret123')
        self.task = Task.objects.create(
            user=self.user,
            title='Prepare presentation',
            status=Task.Status.IN_PROGRESS,
        )

    def test_can_create_task_from_dashboard(self):
        response = self.client.post(
            reverse('todo_dashboard'),
            {
                'form_action': 'create',
                'title': 'Write summary',
                'description': 'Draft the short version',
                'status': Task.Status.TODO,
                'priority': Task.Priority.HIGH,
                'due_date': '',
            },
        )

        self.assertRedirects(response, reverse('todo_dashboard'))
        self.assertTrue(Task.objects.filter(user=self.user, title='Write summary').exists())

    def test_can_toggle_task_status(self):
        response = self.client.post(
            reverse('todo_dashboard'),
            {
                'form_action': 'toggle_status',
                'task_id': self.task.id,
            },
        )

        self.assertRedirects(response, reverse('todo_dashboard'))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)

    def test_can_delete_task(self):
        response = self.client.post(
            reverse('todo_dashboard'),
            {
                'form_action': 'delete',
                'task_id': self.task.id,
            },
        )

        self.assertRedirects(response, reverse('todo_dashboard'))
        self.assertFalse(Task.objects.filter(pk=self.task.id).exists())

    def test_dashboard_defaults_to_todo_filter(self):
        todo_task = Task.objects.create(
            user=self.user,
            title='Todo task',
            status=Task.Status.TODO,
        )

        response = self.client.get(reverse('todo_dashboard'))

        self.assertContains(response, todo_task.title)
        self.assertNotContains(response, self.task.title)

    def test_can_archive_task_from_dashboard(self):
        response = self.client.post(
            reverse('todo_dashboard'),
            {
                'form_action': 'archive',
                'task_id': self.task.id,
            },
        )

        self.assertRedirects(response, reverse('todo_dashboard'))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.ARCHIVED)


class PasswordResetTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(
            username='restore-user',
            email='restore@example.com',
            password='old-secret123',
        )

    def test_password_reset_page_is_available(self):
        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Восстановление доступа')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_request_redirects_to_done_page(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'restore@example.com'},
        )

        self.assertRedirects(response, reverse('password_reset_done'))

    def test_set_password_form_uses_localized_placeholders(self):
        user = get_user_model()(username='restore-user')
        form = TodoSetPasswordForm(user)

        self.assertEqual(
            form.fields['new_password1'].widget.attrs['placeholder'],
            'Новый пароль',
        )


class LegalPageTests(TestCase):
    def test_privacy_policy_page_is_available(self):
        response = self.client.get(reverse('privacy_policy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Политика конфиденциальности')

    def test_terms_page_is_available(self):
        response = self.client.get(reverse('terms'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пользовательское соглашение')


class DonationFlowTests(TestCase):
    def test_donation_page_is_available(self):
        response = self.client.get(reverse('donation_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Донат')

    @override_settings(YOOKASSA_SHOP_ID='shop-id', YOOKASSA_SECRET_KEY='secret-key')
    @patch('todo.views.get_payment_client')
    def test_donation_post_creates_payment_and_redirects_to_confirmation(self, mocked_get_client):
        client = mocked_get_client.return_value
        client.is_configured = True
        client.is_fake = False
        client.provider = 'yookassa'
        client.create_payment.return_value = {
            'id': 'pay_123',
            'status': 'pending',
            'paid': False,
            'confirmation': {
                'confirmation_url': 'https://yookassa.example/confirm',
            },
        }

        response = self.client.post(
            reverse('donation_create'),
            {
                'amount': '100.00',
                'payment_method': Donation.PaymentMethod.BANK_CARD,
                'donor_name': 'Tester',
                'donor_email': 'tester@example.com',
                'message': 'Keep going',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://yookassa.example/confirm')
        donation = Donation.objects.get(provider_payment_id='pay_123')
        self.assertEqual(donation.status, Donation.Status.PENDING)
        client.create_payment.assert_called_once()

    @override_settings(DONATION_FAKE_GATEWAY=True)
    def test_fake_gateway_completes_donation_without_external_service(self):
        response = self.client.post(
            reverse('donation_create'),
            {
                'amount': '100.00',
                'payment_method': Donation.PaymentMethod.ANY,
                'donor_name': 'Local Tester',
                'donor_email': 'local@example.com',
                'message': '',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спасибо за донат')
        donation = Donation.objects.get(provider='mock')
        self.assertEqual(donation.status, Donation.Status.SUCCEEDED)
        self.assertTrue(donation.provider_payment_id.startswith('mock_'))

    @override_settings(YOOKASSA_SHOP_ID='shop-id', YOOKASSA_SECRET_KEY='secret-key')
    @patch('todo.views.get_payment_client')
    def test_return_page_verifies_payment_and_marks_donation_paid(self, mocked_get_client):
        donation = Donation.objects.create(
            amount='300.00',
            status=Donation.Status.PENDING,
            provider_payment_id='pay_456',
        )
        client = mocked_get_client.return_value
        client.is_configured = True
        client.is_fake = False
        client.provider = 'yookassa'
        client.get_payment.return_value = {
            'id': 'pay_456',
            'status': 'succeeded',
            'paid': True,
        }

        response = self.client.get(
            reverse('donation_return', kwargs={'public_id': donation.public_id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спасибо за донат')
        donation.refresh_from_db()
        self.assertEqual(donation.status, Donation.Status.SUCCEEDED)
        self.assertIsNotNone(donation.paid_at)

    def test_webhook_updates_donation_status_idempotently(self):
        donation = Donation.objects.create(
            amount='500.00',
            status=Donation.Status.PENDING,
            provider_payment_id='pay_789',
        )

        response = self.client.post(
            reverse('donation_webhook'),
            data=json.dumps(
                {
                    'type': 'notification',
                    'event': 'payment.succeeded',
                    'object': {
                        'id': 'pay_789',
                        'status': 'succeeded',
                        'paid': True,
                    },
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, Donation.Status.SUCCEEDED)


class TelegramPasswordResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='telegram-user',
            email='telegram@example.com',
            password='secret123',
        )

    def test_telegram_reset_page_is_available(self):
        response = self.client.get(reverse('telegram_password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Сброс через Telegram')

    @override_settings(TELEGRAM_BOT_USERNAME='todo_test_bot')
    def test_telegram_link_page_creates_link_token(self):
        self.client.login(username='telegram-user', password='secret123')

        response = self.client.get(reverse('telegram_link'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://t.me/todo_test_bot?start=')
        self.assertEqual(TelegramLinkToken.objects.filter(user=self.user).count(), 1)

    @override_settings(TELEGRAM_BOT_USERNAME='todo_test_bot')
    def test_signup_redirects_to_telegram_link_when_bot_is_configured(self):
        response = self.client.post(
            reverse('todo_home_list'),
            {
                'form_type': 'register',
                'username': 'new-user',
                'email': 'new@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('telegram_link'))

    @override_settings(TELEGRAM_BOT_USERNAME='todo_test_bot')
    def test_dashboard_requires_telegram_link_when_bot_is_configured(self):
        self.client.login(username='telegram-user', password='secret123')

        response = self.client.get(reverse('todo_dashboard'))

        self.assertRedirects(response, reverse('telegram_link'))

    def test_telegram_webhook_links_account_from_start_token(self):
        raw_token = 'secure-token'
        TelegramLinkToken.objects.create(
            user=self.user,
            token_hash=token_hash(raw_token),
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        response = self.client.post(
            reverse('telegram_webhook'),
            data=json.dumps(
                {
                    'message': {
                        'text': f'/start {raw_token}',
                        'chat': {'id': 123456789},
                        'from': {
                            'id': 123456789,
                            'username': 'todo_user',
                            'first_name': 'Todo',
                        },
                    }
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            TelegramAccount.objects.filter(
                user=self.user,
                chat_id='123456789',
                username='todo_user',
            ).exists()
        )

    @patch('todo.views.send_telegram_message')
    def test_telegram_reset_sends_link_to_linked_chat(self, mocked_send):
        TelegramAccount.objects.create(user=self.user, chat_id='123456789')

        response = self.client.post(
            reverse('telegram_password_reset'),
            {'username_or_email': 'telegram@example.com'},
        )

        self.assertRedirects(response, reverse('telegram_password_reset_done'))
        mocked_send.assert_called_once()
        self.assertIn('/reset/', mocked_send.call_args.args[1])


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='settings-user',
            email='settings@example.com',
            password='old-secret123',
        )
        TelegramAccount.objects.create(user=self.user, chat_id='111222333')
        self.client.login(username='settings-user', password='old-secret123')

    def test_account_settings_page_is_available(self):
        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Настройки аккаунта')

    def test_can_update_account_data(self):
        response = self.client.post(
            reverse('account_settings'),
            {
                'form_action': 'account',
                'username': 'settings-updated',
                'email': 'updated@example.com',
            },
        )

        self.assertRedirects(response, reverse('account_settings'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'settings-updated')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_can_change_password_and_keep_session(self):
        response = self.client.post(
            reverse('account_settings'),
            {
                'form_action': 'password',
                'old_password': 'old-secret123',
                'new_password1': 'new-secret123',
                'new_password2': 'new-secret123',
            },
        )

        self.assertRedirects(response, reverse('account_settings'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-secret123'))

        dashboard_response = self.client.get(reverse('todo_dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
