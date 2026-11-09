from django.db import models
from orders.models import Order


class Transaction(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'در حال انتقال به درگاه'
        SUCCESS = 'success', 'موفق'
        FAILED = 'failed', 'ناموفق / لغو شده توسط کاربر'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='سفارش مربوطه'
    )
    authority = models.CharField('کد Authority زرین‌پال', max_length=64, unique=True)
    amount_toman = models.PositiveBigIntegerField('مبلغ تراکنش (تومان)')
    is_second_stage = models.BooleanField('تراکنش تسویه مرحله دوم (مابقی بیعانه)', default=False)
    ref_id = models.CharField('شماره تراکنش بانکی (Ref ID)', max_length=64, blank=True)
    card_pan = models.CharField('شماره کارت (ماسک شده)', max_length=32, blank=True)
    status = models.CharField(
        'وضعیت تراکنش',
        max_length=15,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField('زمان ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('زمان بروزرسانی', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تراکنش بانکی'
        verbose_name_plural = '۴. تراکنش‌های درگاه پرداخت'

    def __str__(self):
        stage = "مرحله دوم" if self.is_second_stage else "مرحله اول"
        return f"تراکنش {self.order.order_code} ({stage}) - {self.get_status_display()}"