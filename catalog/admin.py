from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductVariant, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'display_order', 'is_active', 'product_count')
    list_display_links = ('image_preview', 'name')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description="تصویر")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 50%; border: 1px solid #ddd;" />',
                obj.image.url
            )
        return "—"

    @admin.display(description="تعداد محصول")
    def product_count(self, obj):
        return obj.products.count()


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 4  # به صورت پیش‌فرض ۴ ردیف خالی برای سایزها نمایش می‌دهد
    fields = ('size_title', 'price_adjustment', 'stock', 'display_order', 'is_active', 'final_price_display')
    readonly_fields = ('final_price_display',)

    @admin.display(description="قیمت نهایی این سایز")
    def final_price_display(self, obj):
        if obj.pk and obj.product_id:
            return f"{obj.get_final_price():,} تومان"
        return "پس از ذخیره محاسبه می‌شود"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    fields = ('image', 'image_preview', 'alt_text', 'display_order')
    readonly_fields = ('image_preview',)

    @admin.display(description="پیش‌نمایش")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 6px;" />',
                obj.image.url
            )
        return "—"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview',
        'name',
        'category',
        'base_price',
        'discount_price',
        'total_stock_display',
        'allow_custom_measurements',
        'is_active',
        'is_featured',
    )
    list_display_links = ('image_preview', 'name')
    list_editable = ('base_price', 'discount_price', 'allow_custom_measurements', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'allow_custom_measurements')
    search_fields = ('name', 'code', 'fabric_details')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline, ProductImageInline]

    fieldsets = (
        ("اطلاعات اصلی محصول", {
            "fields": ("category", "name", "slug", "code", "main_image")
        }),
        ("قیمت‌گذاری پایه", {
            "fields": ("base_price", "discount_price"),
            "description": "قیمت پایه را به تومان وارد کنید. اگر سایز خاصی افزایش قیمت دارد، در جدول پایین صفحه (سایزبندی) مابه‌التفاوت را وارد نمایید."
        }),
        ("مشخصات پارچه و توضیحات", {
            "fields": ("fabric_details", "description")
        }),
        ("تنظیمات شخصی‌دوزی (دوخت سفارشی)", {
            "fields": ("allow_custom_measurements", "custom_measurement_hint")
        }),
        ("وضعیت نمایش", {
            "fields": ("is_active", "is_featured")
        }),
    )

    @admin.display(description="تصویر")
    def image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 60px; object-fit: cover; border-radius: 6px;" />',
                obj.main_image.url
            )
        return "—"

    @admin.display(description="مجموع موجودی")
    def total_stock_display(self, obj):
        stock = obj.total_stock
        if stock == 0:
            return format_html('<span style="color: #dc2626; font-weight: bold;">ناموجود (0)</span>')
        return f"{stock} عدد"