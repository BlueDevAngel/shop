from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'amount_display',
        'status_badge',
        'ref_id',
        'card_pan',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_code', 'order__full_name', 'order__phone', 'authority', 'ref_id')
    readonly_fields = ('order', 'authority', 'amount_toman', 'ref_id', 'card_pan', 'status', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="مبلغ")
    def amount_display(self, obj):
        formatted = f"{obj.amount_toman:,}"
        return f"{formatted} تومان"

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        if obj.status == Transaction.StatusChoices.SUCCESS:
            return format_html('<span style="color: #15803d; font-weight: bold;">{}</span>', 'موفق ✓')
        elif obj.status == Transaction.StatusChoices.FAILED:
            return format_html('<span style="color: #b91c1c;">{}</span>', 'ناموفق ✕')
        return format_html('<span style="color: #b45309;">{}</span>', 'در انتظار')