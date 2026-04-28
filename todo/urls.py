from django.contrib.auth import views as auth_views
from django.urls import path

from todo.forms import TodoPasswordResetForm, TodoSetPasswordForm
from todo import views


urlpatterns = [
    path('', views.todo_home_list, name='todo_home_list'),
    path('tasks/', views.todo_dashboard, name='todo_dashboard'),
    path('logout/', views.todo_logout, name='todo_logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            form_class=TodoPasswordResetForm,
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            form_class=TodoSetPasswordForm,
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
