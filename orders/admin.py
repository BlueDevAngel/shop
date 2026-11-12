from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'size_title', 'unit_price_display', 'quantity', 'custom_measurements', 'total_display')
    fields = ('product_name', 'size_title', 'unit_price_display', 'quantity', 'custom_measurements', 'total_display')
    can_delete = False

    @admin.display(description="قیمت واحد")
    def unit_price_display(self, obj):
        if obj.unit_price is None:
            return "—"
        return f"{obj.unit_price:,} تومان"

    @admin.display(description="جمع ردیف")
    def total_display(self, obj):
        if obj.unit_price is None or obj.quantity is None:
            return "—"
        return f"{obj.get_total_price():,} تومان"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_code',
        'full_name',
        'phone',
        'city',
        'payment_type',
        'total_amount_display',
        'paid_amount_display',
        'remaining_amount_display',
        'status',
        'tracking_code',
        'print_label_link',
    )
    list_editable = ('status', 'tracking_code')
    list_filter = ('status', 'payment_type', 'created_at', 'province')
    search_fields = ('order_code', 'full_name', 'phone', 'tracking_code')
    readonly_fields = ('order_code', 'access_token', 'items_total', 'shipping_cost', 'total_amount', 'payable_now', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    fieldsets = (
        ("وضعیت و کد رهگیری مرسوله", {
            "fields": ("order_code", "status", "payment_type", "tracking_code", "created_at")
        }),
        ("مشخصات و آدرس مشتری", {
            "fields": ("full_name", "phone", "province", "city", "address", "postal_code", "customer_note")
        }),
        ("جزئیات مالی (تومان)", {
            "fields": ("items_total", "shipping_cost", "total_amount", "payable_now", "paid_amount")
        }),
    )

    @admin.display(description="مبلغ کل فاکتور")
    def total_amount_display(self, obj):
        return f"{obj.total_amount:,} ت"

    @admin.display(description="پرداخت شده")
    def paid_amount_display(self, obj):
        formatted_price = f"{obj.paid_amount:,}"
        return format_html('<span style="color: #15803d; font-weight: bold;">{} ت</span>', formatted_price)

    @admin.display(description="مانده حساب")
    def remaining_amount_display(self, obj):
        rem = obj.remaining_amount
        if rem > 0:
            formatted_rem = f"{rem:,}"
            return format_html('<span style="color: #b91c1c; font-weight: bold;">{} ت</span>', formatted_rem)
        return "تسویه کامل"

    @admin.display(description="چاپ برچسب")
    def print_label_link(self, obj):
        url = reverse('orders:shipping_label', args=[obj.access_token])
        return format_html(
            '<a href="{}" target="_blank" style="background:#2A211D; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; text-decoration:none;">چاپ برچسب</a>',
            url
        )