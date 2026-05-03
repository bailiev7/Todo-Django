from django.contrib.auth import views as auth_views
from django.urls import path

from todo.forms import TodoPasswordResetForm, TodoSetPasswordForm
from todo import views


urlpatterns = [
    path('', views.todo_home_list, name='todo_home_list'),
    path('donate/', views.donation_create, name='donation_create'),
    path('donate/return/<uuid:public_id>/', views.donation_return, name='donation_return'),
    path('donate/webhook/', views.donation_webhook, name='donation_webhook'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms, name='terms'),
    path('telegram/link/', views.telegram_link, name='telegram_link'),
    path('telegram/reset/', views.telegram_password_reset, name='telegram_password_reset'),
    path(
        'telegram/reset/done/',
        views.telegram_password_reset_done,
        name='telegram_password_reset_done',
    ),
    path('telegram/webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('account/settings/', views.account_settings, name='account_settings'),
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
