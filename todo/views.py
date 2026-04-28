from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from todo.forms import EmailAuthenticationForm, SignUpForm, TaskForm
from todo.models import Task


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
                return redirect(f"{reverse('todo_dashboard')}?welcome=1")
        else:
            login_form = EmailAuthenticationForm(request=request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                messages.success(request, 'С возвращением!')
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


@login_required
def todo_dashboard(request):
    edit_task = None
    status_filter = request.GET.get('status', 'all')
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
                ('all', 'Все'),
                (Task.Status.TODO, Task.Status.TODO.label),
                (Task.Status.IN_PROGRESS, Task.Status.IN_PROGRESS.label),
                (Task.Status.DONE, Task.Status.DONE.label),
                (Task.Status.ARCHIVED, Task.Status.ARCHIVED.label),
            ],
        },
    )


@login_required
def todo_logout(request):
    logout(request)
    return redirect('todo_home_list')
