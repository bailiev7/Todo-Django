import hashlib
import json
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from todo.forms import (
    AccountUpdateForm,
    DonationForm,
    EmailAuthenticationForm,
    SignUpForm,
    TaskForm,
    TodoPasswordChangeForm,
    TelegramPasswordResetForm,
)
from todo.models import Donation, Task, TelegramAccount, TelegramLinkToken
from todo.payments import PaymentGatewayError, get_payment_client
from todo.telegram import TelegramSendError, send_telegram_message


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def suggested_donation_amounts():
    amounts = []

    for value in settings.DONATION_SUGGESTED_AMOUNTS:
        try:
            amount = Decimal(value).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            continue
        amounts.append({'value': f'{amount:.2f}', 'label': f'{amount:,.0f} ₽'.replace(',', ' ')})

    return amounts


def sync_donation_from_payment(donation, payment):
    status = payment.get('status')
    donation.provider_payment_id = payment.get('id') or donation.provider_payment_id
    donation.provider_payload = payment

    confirmation = payment.get('confirmation') or {}
    if confirmation.get('confirmation_url'):
        donation.confirmation_url = confirmation['confirmation_url']

    if status == 'succeeded' or payment.get('paid') is True:
        donation.status = Donation.Status.SUCCEEDED
        if donation.paid_at is None:
            donation.paid_at = timezone.now()
    elif status == 'canceled':
        donation.status = Donation.Status.CANCELED
    elif status:
        donation.status = Donation.Status.PENDING

    donation.save()
    return donation


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def verify_yookassa_webhook_request(request):
    allowed_ips = set(settings.YOOKASSA_WEBHOOK_IPS)
    if not allowed_ips:
        return True
    return get_client_ip(request) in allowed_ips


def verify_telegram_webhook_request(request):
    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not expected_secret:
        return not settings.TELEGRAM_BOT_TOKEN
    return request.headers.get('X-Telegram-Bot-Api-Secret-Token') == expected_secret


def todo_home_list(request):
    if request.user.is_authenticated:
        return redirect('todo_dashboard')

    login_form = EmailAuthenticationForm(request=request)
    signup_form = SignUpForm()
    active_form = request.GET.get('tab', 'login')

    if request.method == 'POST':
        active_form = request.POST.get('form_type', 'login')

        if active_form == 'register':
            signup_form = SignUpForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)
                messages.success(request, 'Аккаунт успешно создан.')
                if settings.TELEGRAM_BOT_USERNAME:
                    return redirect('telegram_link')
                return redirect(f"{reverse('todo_dashboard')}?welcome=1")
        else:
            login_form = EmailAuthenticationForm(request=request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                messages.success(request, 'С возвращением!')
                if settings.TELEGRAM_BOT_USERNAME:
                    try:
                        user.telegram_account
                    except TelegramAccount.DoesNotExist:
                        messages.info(
                            request,
                            'Привяжите Telegram, чтобы получать ссылки для сброса пароля через бота.',
                        )
                return redirect(f"{reverse('todo_dashboard')}?welcome=1")

    context = {
        'login_form': login_form,
        'signup_form': signup_form,
        'active_form': active_form,
        'login_error': login_form.errors if active_form == 'login' else None,
        'signup_error': signup_form.errors if active_form == 'register' else None,
    }
    return render(request, 'todo/todo_home_list.html', context)


def privacy_policy(request):
    return render(request, 'Privacy-terms/privacy_policy.html')


def terms(request):
    return render(request, 'Privacy-terms/terms.html')


def donation_create(request):
    client = get_payment_client()
    initial = {}

    if request.user.is_authenticated:
        initial = {
            'donor_name': request.user.get_full_name() or request.user.get_username(),
            'donor_email': request.user.email,
        }

    form = DonationForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        if not client.is_configured:
            messages.error(
                request,
                'Платежный шлюз пока не настроен. Добавьте ключи ЮKassa в .env и повторите попытку.',
            )
        else:
            donation = form.save(commit=False)
            donation.user = request.user if request.user.is_authenticated else None
            donation.currency = settings.DONATION_CURRENCY
            donation.provider = client.provider
            donation.save()
            return_url = request.build_absolute_uri(
                reverse('donation_return', kwargs={'public_id': donation.public_id})
            )

            try:
                payment = client.create_payment(donation, return_url)
            except PaymentGatewayError as exc:
                donation.status = Donation.Status.CANCELED
                donation.provider_payload = {'error': str(exc)}
                donation.save(update_fields=['status', 'provider_payload', 'updated_at'])
                messages.error(request, 'Не удалось создать платеж. Проверьте настройки ЮKassa.')
            else:
                sync_donation_from_payment(donation, payment)

                if donation.confirmation_url:
                    return redirect(donation.confirmation_url)
                return redirect('donation_return', public_id=donation.public_id)

    return render(
        request,
        'todo/donation_form.html',
        {
            'form': form,
            'payment_configured': client.is_configured,
            'fake_gateway': client.is_fake,
            'suggested_amounts': suggested_donation_amounts(),
        },
    )


def donation_return(request, public_id):
    donation = get_object_or_404(Donation, public_id=public_id)
    client = get_payment_client(provider=donation.provider)

    if donation.provider_payment_id and client.is_configured:
        try:
            payment = client.get_payment(donation.provider_payment_id)
        except PaymentGatewayError:
            messages.warning(request, 'Не удалось обновить статус платежа. Попробуйте обновить страницу позже.')
        else:
            sync_donation_from_payment(donation, payment)

    return render(request, 'todo/donation_thanks.html', {'donation': donation})


@csrf_exempt
@require_POST
def donation_webhook(request):
    if not verify_yookassa_webhook_request(request):
        return HttpResponseForbidden('Forbidden')

    try:
        payload = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    payment = payload.get('object') or {}
    payment_id = payment.get('id')

    if not payment_id:
        return HttpResponseBadRequest('Payment id required')

    donation = Donation.objects.filter(provider_payment_id=payment_id).first()
    if donation is None:
        public_id = (payment.get('metadata') or {}).get('public_id')
        if public_id:
            donation = Donation.objects.filter(public_id=public_id).first()

    if donation is None:
        return JsonResponse({'ok': True})

    client = get_payment_client(provider=donation.provider)
    if client.is_configured:
        try:
            payment = client.get_payment(payment_id)
        except PaymentGatewayError:
            return JsonResponse({'ok': False}, status=502)

    sync_donation_from_payment(donation, payment)
    return JsonResponse({'ok': True})


@login_required
def telegram_link(request):
    if not settings.TELEGRAM_BOT_USERNAME:
        messages.error(request, 'Telegram bot пока не настроен.')
        return redirect('todo_dashboard')

    raw_token = secrets.token_urlsafe(32)
    TelegramLinkToken.objects.create(
        user=request.user,
        token_hash=token_hash(raw_token),
        expires_at=timezone.now() + timedelta(minutes=30),
    )
    bot_url = f'https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={raw_token}'

    return render(
        request,
        'todo/telegram_link.html',
        {
            'bot_url': bot_url,
            'expires_minutes': 30,
            'telegram_account': getattr(request.user, 'telegram_account', None),
        },
    )


def telegram_password_reset(request):
    form = TelegramPasswordResetForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['username_or_email'].strip()
        user = (
            get_user_model()
            .objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
            .first()
        )

        if user:
            try:
                telegram_account = user.telegram_account
            except TelegramAccount.DoesNotExist:
                telegram_account = None

            if telegram_account:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse(
                        'password_reset_confirm',
                        kwargs={'uidb64': uid, 'token': token},
                    )
                )
                text = (
                    '✅ Запрошен сброс пароля для Todo Home List.\n\n'
                    f'Откройте ссылку и задайте новый пароль:\n{reset_url}\n\n'
                    'Если вы не запрашивали сброс пароля, просто проигнорируйте это сообщение.'
                )

                try:
                    send_telegram_message(telegram_account.chat_id, text)
                except TelegramSendError:
                    pass

        return redirect('telegram_password_reset_done')

    return render(request, 'registration/telegram_password_reset_form.html', {'form': form})


def telegram_password_reset_done(request):
    return render(request, 'registration/telegram_password_reset_done.html')


@csrf_exempt
def telegram_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    if not verify_telegram_webhook_request(request):
        return HttpResponseForbidden('Forbidden')

    try:
        update = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    message = update.get('message') or {}
    text = (message.get('text') or '').strip()
    chat = message.get('chat') or {}
    from_user = message.get('from') or {}

    if not text.startswith('/start '):
        if chat.get('id'):
            try:
                send_telegram_message(
                    chat['id'],
                    'Откройте ссылку привязки Telegram из личного кабинета Todo Home List.',
                )
            except TelegramSendError:
                pass
        return JsonResponse({'ok': True})

    raw_token = text.split(maxsplit=1)[1].strip()
    link_token = TelegramLinkToken.objects.filter(token_hash=token_hash(raw_token)).first()

    if not link_token or not link_token.is_active:
        if chat.get('id'):
            try:
                send_telegram_message(
                    chat['id'],
                    'Ссылка привязки недействительна или устарела. Создайте новую ссылку в аккаунте.',
                )
            except TelegramSendError:
                pass
        return JsonResponse({'ok': True})

    TelegramAccount.objects.filter(chat_id=str(chat.get('id'))).exclude(
        user=link_token.user
    ).delete()
    TelegramAccount.objects.update_or_create(
        user=link_token.user,
        defaults={
            'chat_id': str(chat.get('id')),
            'username': from_user.get('username', ''),
            'first_name': from_user.get('first_name', ''),
        },
    )
    link_token.used_at = timezone.now()
    link_token.save(update_fields=['used_at'])

    try:
        send_telegram_message(
            chat['id'],
            '✅ Telegram успешно привязан к аккаунту Todo Home List. Теперь можно получать ссылки для сброса пароля здесь.',
        )
    except TelegramSendError:
        pass

    return JsonResponse({'ok': True})


@login_required
def account_settings(request):
    account_form = AccountUpdateForm(instance=request.user)
    password_form = TodoPasswordChangeForm(request.user)

    if request.method == 'POST':
        form_action = request.POST.get('form_action')

        if form_action == 'account':
            account_form = AccountUpdateForm(request.POST, instance=request.user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, 'Данные аккаунта обновлены.')
                return redirect('account_settings')
            messages.error(request, 'Проверьте данные аккаунта.')
        elif form_action == 'password':
            password_form = TodoPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменен.')
                return redirect('account_settings')
            messages.error(request, 'Проверьте поля смены пароля.')

    return render(
        request,
        'todo/account_settings.html',
        {
            'account_form': account_form,
            'password_form': password_form,
            'telegram_account': getattr(request.user, 'telegram_account', None),
        },
    )


@login_required
def todo_dashboard(request):
    if settings.TELEGRAM_BOT_USERNAME:
        try:
            request.user.telegram_account
        except TelegramAccount.DoesNotExist:
            messages.info(
                request,
                'Telegram не привязан. Задачи доступны, а восстановление пароля через бота можно включить в настройках аккаунта.',
            )

    edit_task = None
    status_filter = request.GET.get('status', Task.Status.TODO)
    run_blur = request.GET.get('welcome') == '1'

    if request.method == 'POST':
        form_action = request.POST.get('form_action', 'create')

        if form_action == 'delete':
            task = get_object_or_404(
                Task,
                pk=request.POST.get('task_id'),
                user=request.user,
            )
            task.delete()
            messages.success(request, 'Задача удалена.')
            return redirect('todo_dashboard')
        elif form_action == 'toggle_status':
            task = get_object_or_404(
                Task,
                pk=request.POST.get('task_id'),
                user=request.user,
            )
            if task.status == Task.Status.DONE:
                task.status = Task.Status.IN_PROGRESS
                messages.success(request, 'Статус изменён на "В процессе".')
            else:
                task.status = Task.Status.DONE
                messages.success(request, 'Статус изменён на "Сделано".')
            task.save()
            return redirect('todo_dashboard')
        elif form_action == 'archive':
            task = get_object_or_404(
                Task,
                pk=request.POST.get('task_id'),
                user=request.user,
            )
            task.status = Task.Status.ARCHIVED
            task.save()
            messages.success(request, 'Задача отправлена в архив.')
            return redirect('todo_dashboard')
        elif form_action == 'update':
            edit_task = get_object_or_404(
                Task,
                pk=request.POST.get('task_id'),
                user=request.user,
            )
            task_form = TaskForm(request.POST, instance=edit_task)
            if task_form.is_valid():
                task_form.save()
                messages.success(request, 'Задача обновлена.')
                return redirect('todo_dashboard')
            messages.error(request, 'Проверьте поля формы и попробуйте снова.')
        else:
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.user = request.user
                task.save()
                messages.success(request, 'Задача создана.')
                return redirect('todo_dashboard')
            messages.error(request, 'Не удалось создать задачу. Проверьте форму.')
    else:
        edit_id = request.GET.get('edit')
        if edit_id:
            edit_task = get_object_or_404(Task, pk=edit_id, user=request.user)
            task_form = TaskForm(instance=edit_task)
        else:
            task_form = TaskForm()

    tasks = Task.objects.filter(user=request.user)
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    tasks = tasks.order_by('status', '-priority', 'due_date')

    return render(
        request,
        'todo/todo_dashboard.html',
        {
            'tasks': tasks,
            'task_form': task_form,
            'edit_task': edit_task,
            'status_filter': status_filter,
            'run_blur': run_blur,
            'status_choices': [
                (Task.Status.TODO, Task.Status.TODO.label),
                (Task.Status.IN_PROGRESS, Task.Status.IN_PROGRESS.label),
                (Task.Status.DONE, Task.Status.DONE.label),
                (Task.Status.ARCHIVED, Task.Status.ARCHIVED.label),
                ('all', 'Все'),
            ],
        },
    )


@login_required
def todo_logout(request):
    logout(request)
    return redirect('todo_home_list')
