from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from todo.forms import TaskForm, TodoSetPasswordForm
from todo.models import Task


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
