from django.contrib import admin
from .models import Ad, ExchangeProposal
@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'condition', 'created_at')
    search_fields = ('title', 'description', 'category')
    list_filter = ('condition', 'category')
    ordering = ('-created_at',)

admin.site.register(ExchangeProposal)