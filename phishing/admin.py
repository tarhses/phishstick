from django.contrib import admin

from phishing.models import Target, TargetPool


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['id', 'sent_at', 'opened_at', 'clicked_at', 'phished_at']
    actions = ['reset']

    @admin.action(description='Reset selected targets')
    def reset(self, request, queryset):
        queryset.update(sent_at=None, opened_at=None, clicked_at=None, phished_at=None)


@admin.register(TargetPool)
class TargetPoolAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'template', 'sent_count', 'opened_count', 'clicked_count', 'phished_count']
    ordering = ['group', 'template']
    actions = ['reset']

    @admin.action(description='Reset selected pools')
    def reset(self, request, queryset):
        queryset.update(sent_count=0, opened_count=0, clicked_count=0, phished_count=0)
