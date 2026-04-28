from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.utils import timezone

from todo.models import Task


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {
                'placeholder': 'Имя пользователя',
                'autocomplete': 'username',
                'aria-label': 'Username',
            }
        )
        self.fields['email'].widget.attrs.update(
            {
                'placeholder': 'Электронная почта',
                'autocomplete': 'email',
                'aria-label': 'Email address',
            }
        )
        self.fields['password1'].widget.attrs.update(
            {
                'placeholder': 'Ваш пароль',
                'autocomplete': 'new-password',
                'aria-label': 'Create a password',
            }
        )
        self.fields['password2'].widget.attrs.update(
            {
                'placeholder': 'Подтвердить пароль',
                'autocomplete': 'new-password',
                'aria-label': 'Repeat password',
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Имя пользователя',
                'autocomplete': 'username',
                'aria-label': 'Username',
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Пароль',
                'autocomplete': 'current-password',
                'aria-label': 'Password',
            }
        )
    )


class TodoPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Электронная почта',
                'autocomplete': 'email',
                'aria-label': 'Электронная почта',
            }
        )
    )


class TodoSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['new_password1'].widget.attrs.update(
            {
                'placeholder': 'Новый пароль',
                'autocomplete': 'new-password',
                'aria-label': 'Новый пароль',
            }
        )
        self.fields['new_password2'].widget.attrs.update(
            {
                'placeholder': 'Повторите новый пароль',
                'autocomplete': 'new-password',
                'aria-label': 'Повторите новый пароль',
            }
        )


class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')

        if due_date and due_date < timezone.localdate():
            raise forms.ValidationError(
                'Срок выполнения не может быть раньше текущей даты.'
            )

        return due_date

    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority', 'due_date')
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Название задачи',
                    'aria-label': 'Название задачи',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Описание задачи',
                    'aria-label': 'Описание задачи',
                    'rows': 4,
                }
            ),
            'status': forms.Select(
                attrs={'aria-label': 'Статус задачи'}
            ),
            'priority': forms.Select(
                attrs={'aria-label': 'Приоритет задачи'}
            ),
            'due_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'aria-label': 'Срок выполнения',
                }
            ),
        }
