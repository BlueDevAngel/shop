import uuid
import re
from django.db import models
from django.core.exceptions import ValidationError
from catalog.models import Product, ProductVariant


def validate_iranian_phone(value):
    if not re.match(r'^09\d{9}$', value):
        raise ValidationError("شماره موبایل باید ۱۱ رقم و با 09 شروع شود (مثال: 09123456789).")


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        PARTIALLY_PAID = 'partially_paid', 'پرداخت بیعانه (در حال دوخت/آماده‌سازی)'
        PAID = 'paid', 'تسویه کامل (در حال آماده‌سازی)'
        SHIPPED = 'shipped', 'ارسال شده'
        CANCELED = 'canceled', 'لغو شده'

    class PaymentTypeChoices(models.TextChoices):
        FULL = 'full', 'پرداخت کامل'
        DEPOSIT = 'deposit', 'پرداخت دومرحله‌ای (بیعانه)'

    # کد پیگیری کوتاه و خوانا برای مشتری و کلید امنیتی UUID برای لینک‌ها
    order_code = models.CharField("کد سفارش", max_length=20, unique=True, editable=False)
    access_token = models.UUIDField("توکن امنیتی دسترسی", default=uuid.uuid4, editable=False, unique=True)

    # مشخصات گیرنده
    full_name = models.CharField("نام و نام خانوادگی تحویل‌گیرنده", max_length=120)
    phone = models.CharField("شماره موبایل", max_length=11, validators=[validate_iranian_phone])
    province = models.CharField("استان", max_length=60)
    city = models.CharField("شهر", max_length=60)
    address = models.TextField("آدرس دقیق پستی")
    postal_code = models.CharField("کد پستی (۱۰ رقمی)", max_length=10, blank=True)
    customer_note = models.TextField("یادداشت مشتری برای سفارش (اختیاری)", blank=True)

    # اطلاعات مالی (تماماً به تومان و محاسبه شده در سمت سرور)
    payment_type = models.CharField(
        "نوع پرداخت انتخابی",
        max_length=15,
        choices=PaymentTypeChoices.choices,
        default=PaymentTypeChoices.FULL
    )
    items_total = models.PositiveBigIntegerField("جمع کل اقلام (تومان)", default=0)
    shipping_cost = models.PositiveBigIntegerField("هزینه ارسال (تومان)", default=0)
    total_amount = models.PositiveBigIntegerField("مبلغ کل فاکتور (تومان)", default=0)
    payable_now = models.PositiveBigIntegerField("مبلغ قابل پرداخت در درگاه (تومان)", default=0)
    paid_amount = models.PositiveBigIntegerField("مبلغ پرداخت شده تا این لحظه (تومان)", default=0)

    status = models.CharField("وضعیت سفارش", max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    tracking_code = models.CharField("کد رهگیری پست / تیپاکس", max_length=50, blank=True)

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "سفارش"
        verbose_name_plural = "۳. سفارش‌های مشتریان"

    def save(self, *args, **kwargs):
        if not self.order_code:
            # تولید کد سفارش خوانا مثل MN-482910
            random_digits = str(uuid.uuid4().int)[:6]
            self.order_code = f"MN-{random_digits}"
        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        """مبلغ باقی‌مانده جهت تسویه (مخصوص پرداخت دومرحله‌ای)"""
        rem = self.total_amount - self.paid_amount
        return max(rem, 0)

    def __str__(self):
        return f"سفارش {self.order_code} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="سفارش")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="محصول")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name="سایز انتخابی")
    
    # ذخیره یک کپی ثابت از نام، سایز و قیمت در لحظه خرید (تا اگر ادمین فردا قیمت را تغییر داد، فاکتور قبلی تغییر نکند)
    product_name = models.CharField("نام محصول در زمان خرید", max_length=200)
    size_title = models.CharField("سایز در زمان خرید", max_length=50)
    unit_price = models.PositiveBigIntegerField("قیمت واحد نهایی (تومان)")
    quantity = models.PositiveSmallIntegerField("تعداد", default=1)
    custom_measurements = models.TextField("اندازه‌های شخصی‌دوزی مشتری", blank=True)

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "اقلام سفارش"

    def get_total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_name} ({self.size_title}) × {self.quantity}"