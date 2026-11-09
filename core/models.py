from django.db import models
from django.core.exceptions import ValidationError
from .validators import validate_image_security


class SiteSetting(models.Model):
    site_name = models.CharField("نام فروشگاه", max_length=100, default="مزون لباس")
    tagline = models.CharField("شعار کوتاه (زیرعنوان)", max_length=200, blank=True, default="استایل‌های شیک و کاربردی زنانه")
    logo = models.ImageField("لوگو", upload_to="site/", validators=[validate_image_security], blank=True, null=True)
    announcement_bar = models.CharField("متن نوار اعلان بالای سایت", max_length=250, blank=True, help_text="مثال: ارسال سریع به سراسر ایران | پرداخت دومرحله‌ای")
    
    # Hero Section
    hero_title = models.CharField("تیتر بنر اصلی", max_length=150, default="کالکشن جدید")
    hero_subtitle = models.CharField("زیرنویس بنر اصلی", max_length=250, blank=True)
    hero_image = models.ImageField("تصویر بنر اصلی", upload_to="site/", validators=[validate_image_security], blank=True, null=True)
    
    # Contact & Socials
    instagram_id = models.CharField("آیدی اینستاگرام (بدون @)", max_length=100, blank=True)
    whatsapp_number = models.CharField("شماره واتساپ (با 98، مثال: 989120000000)", max_length=20, blank=True)
    phone_number = models.CharField("شماره تماس پشتیبانی", max_length=20, blank=True)
    address = models.TextField("آدرس فرستنده (نمایش در فوتر و برچسب پستی)", blank=True)
    
    # Shipping & Two-Stage Payment Rules
    shipping_cost = models.PositiveIntegerField("هزینه ارسال ثابت (تومان)", default=70000)
    free_shipping_threshold = models.PositiveIntegerField("حداقل خرید برای ارسال رایگان (تومان، ۰ یعنی غیرفعال)", default=0)
    enable_two_stage_payment = models.BooleanField("فعال‌سازی گزینه پرداخت دو مرحله‌ای (بیعانه)", default=True)
    deposit_percentage = models.PositiveSmallIntegerField("درصد پیش‌پرداخت در خرید دو مرحله‌ای", default=50, help_text="عددی بین 10 تا 90")

    # Size Guide (Modal)
    size_guide_text = models.TextField(
        "متن راهنمای انتخاب سایز",
        blank=True,
        default="سایز ۳۶: دور سینه ۸۴-۸۸ | دور کمر ۶۸-۷۲\nسایز ۳۸: دور سینه ۸۸-۹۲ | دور کمر ۷۲-۷۶\nسایز ۴۰: دور سینه ۹۲-۹۶ | دور کمر ۷۶-۸۰\nسایز ۴۲: دور سینه ۹۶-۱۰۰ | دور کمر ۸۰-۸۴\nسایز ۴۴: دور سینه ۱۰۰-۱۰۶ | دور کمر ۸۴-۹۰"
    )
    size_guide_image = models.ImageField(
        "تصویر جدول سایزبندی (اختیاری)",
        upload_to="site/",
        validators=[validate_image_security],
        blank=True,
        null=True
    )

    # Legal & eNamad
    about_us = models.TextField(
        "متن درباره ما",
        blank=True,
        default="ما با هدف ارائه استایل‌های شیک، کاربردی و دوخت باکیفیت فعالیت می‌کنیم. تمامی سفارش‌ها با دقت بالا و امکان شخصی‌دوزی بر اساس سایز شما آماده می‌شوند."
    )
    terms_and_conditions = models.TextField(
        "قوانین و شرایط ثبت سفارش و ارسال",
        blank=True,
        default="۱. زمان آماده‌سازی و ارسال سفارش‌ها بین ۳ تا ۷ روز کاری است.\n۲. در سفارش‌های دارای پرداخت دومرحله‌ای، تسویه مابقی مبلغ پیش از ارسال مرسوله انجام می‌شود.\n۳. سفارش‌هایی که بر اساس اندازه‌های شخصی مشتری (شخصی‌دوزی) دوخته می‌شوند، امکان مرجوعی سلیقه‌ای ندارند."
    )
    enamad_html_code = models.TextField(
        "کد HTML نماد اعتماد (اینماد)",
        blank=True,
        help_text="کد دریافتی از سامانه اینماد را عیناً در این کادر قرار دهید تا در فوتر سایت نمایش داده شود."
    )

    class Meta:
        verbose_name = "تنظیمات کلی سایت"
        verbose_name_plural = "تنظیمات کلی سایت"

    def clean(self):
        if not self.pk and SiteSetting.objects.exists():
            raise ValidationError("فقط یک تنظیمات کلی برای سایت قابل تعریف است. لطفاً همان مورد موجود را ویرایش کنید.")
        if not (10 <= self.deposit_percentage <= 90):
            raise ValidationError("درصد پیش‌پرداخت باید بین ۱۰ تا ۹۰ درصد باشد.")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"تنظیمات فروشگاه ({self.site_name})"