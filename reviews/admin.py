"""Reviews admin."""
from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'consumer', 'farmer', 'rating', 'is_moderated', 'created_at']
    list_filter = ['rating', 'is_moderated']
    search_fields = ['consumer__name', 'farmer__name', 'comment']
    ordering = ['-created_at']
    actions = ['moderate_reviews']

    @admin.action(description='Toggle moderation flag')
    def moderate_reviews(self, request, queryset):
        for rev in queryset:
            rev.is_moderated = not rev.is_moderated
            rev.save()
