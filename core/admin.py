from django.contrib import admin
from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("هویت برند و اعلان‌ها", {
            "fields": ("site_name", "tagline", "logo", "announcement_bar")
        }),
        ("بنر اصلی صفحه اول (Hero)", {
            "fields": ("hero_title", "hero_subtitle", "hero_image")
        }),
        ("قوانین ارسال و پرداخت دو مرحله‌ای", {
            "fields": ("shipping_cost", "free_shipping_threshold", "enable_two_stage_payment", "deposit_percentage")
        }),
        ("راهنمای سایزبندی (نمایش در صفحه محصول)", {
            "fields": ("size_guide_text", "size_guide_image")
        }),
        ("قوانین، درباره ما و کد اینماد", {
            "fields": ("about_us", "terms_and_conditions", "enamad_html_code")
        }),
        ("راه‌های ارتباطی و آدرس فرستنده", {
            "fields": ("instagram_id", "whatsapp_number", "phone_number", "address")
        }),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False