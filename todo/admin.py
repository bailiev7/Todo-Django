from django.contrib import admin

from todo.models import Task


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
