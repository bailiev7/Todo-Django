from django.contrib import admin

from todo.models import Donation, Task, TelegramAccount, TelegramLinkToken


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'status',
        'priority',
        'due_date',
        'completed_at',
        'created_at',
    )
    list_filter = ('status', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    autocomplete_fields = ('user',)
    ordering = ('status', 'due_date', '-created_at')


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_id', 'username', 'linked_at')
    search_fields = ('user__username', 'user__email', 'chat_id', 'username')
    readonly_fields = ('linked_at', 'updated_at')


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'used_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'amount',
        'currency',
        'status',
        'payment_method',
        'donor_email',
        'provider_payment_id',
        'created_at',
        'paid_at',
    )
    list_filter = ('status', 'payment_method', 'provider', 'created_at')
    search_fields = (
        'donor_name',
        'donor_email',
        'provider_payment_id',
        'public_id',
        'user__username',
        'user__email',
    )
    readonly_fields = (
        'public_id',
        'idempotence_key',
        'provider_payment_id',
        'confirmation_url',
        'provider_payload',
        'created_at',
        'updated_at',
        'paid_at',
    )
    autocomplete_fields = ('user',)
    ordering = ('-created_at',)
