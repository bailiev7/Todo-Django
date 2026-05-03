from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.utils import timezone

from todo.models import Donation, Task


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


class TelegramPasswordResetForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=254,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Имя пользователя или email',
                'autocomplete': 'username',
                'aria-label': 'Имя пользователя или email',
            }
        ),
    )


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'placeholder': 'Имя пользователя',
                    'autocomplete': 'username',
                    'aria-label': 'Имя пользователя',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'Электронная почта',
                    'autocomplete': 'email',
                    'aria-label': 'Электронная почта',
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        exists = User.objects.exclude(pk=self.instance.pk).filter(
            username__iexact=username,
        ).exists()

        if exists:
            raise forms.ValidationError('Пользователь с таким именем уже существует.')

        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        exists = User.objects.exclude(pk=self.instance.pk).filter(
            email__iexact=email,
        ).exists()

        if exists:
            raise forms.ValidationError('Пользователь с такой почтой уже существует.')

        return email


class TodoPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['old_password'].widget.attrs.update(
            {
                'placeholder': 'Текущий пароль',
                'autocomplete': 'current-password',
                'aria-label': 'Текущий пароль',
            }
        )
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


class DonationForm(forms.ModelForm):
    amount = forms.DecimalField(
        min_value=Decimal('1.00'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                'placeholder': 'Сумма доната',
                'aria-label': 'Сумма доната',
                'min': '1',
                'step': '1',
                'inputmode': 'decimal',
            }
        ),
    )

    class Meta:
        model = Donation
        fields = (
            'amount',
            'payment_method',
            'donor_name',
            'donor_email',
            'message',
        )
        widgets = {
            'payment_method': forms.RadioSelect,
            'donor_name': forms.TextInput(
                attrs={
                    'placeholder': 'Имя',
                    'autocomplete': 'name',
                    'aria-label': 'Имя',
                }
            ),
            'donor_email': forms.EmailInput(
                attrs={
                    'placeholder': 'Email для уведомления',
                    'autocomplete': 'email',
                    'aria-label': 'Email для уведомления',
                }
            ),
            'message': forms.Textarea(
                attrs={
                    'placeholder': 'Сообщение',
                    'aria-label': 'Сообщение',
                    'rows': 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].min_value = settings.DONATION_MIN_AMOUNT
        self.fields['amount'].max_value = settings.DONATION_MAX_AMOUNT
        self.fields['amount'].widget.attrs.update(
            {
                'min': str(self.fields['amount'].min_value),
                'max': str(self.fields['amount'].max_value),
            }
        )
        self.fields['payment_method'].choices = Donation.PaymentMethod.choices

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
