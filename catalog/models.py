from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from core.validators import validate_image_security


class Category(models.Model):
    name = models.CharField("نام دسته‌بندی", max_length=100)
    slug = models.SlugField("نامک (آدرس در لینک)", max_length=120, unique=True, allow_unicode=True, blank=True)
    image = models.ImageField(
        "تصویر دایره‌ای (سبک هایلایت)",
        upload_to="categories/",
        validators=[validate_image_security],
        blank=True,
        null=True
    )
    display_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0, help_text="عدد کمتر اول نمایش داده می‌شود")
    is_active = models.BooleanField("فعال / نمایش در سایت", default=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "۱. دسته‌بندی‌ها"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="دسته‌بندی"
    )
    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField("نامک (آدرس در لینک)", max_length=220, unique=True, allow_unicode=True, blank=True)
    code = models.CharField("کد یا شناسه محصول (اختیاری)", max_length=50, blank=True)
    
    main_image = models.ImageField(
        "تصویر اصلی محصول",
        upload_to="products/main/",
        validators=[validate_image_security]
    )
    
    base_price = models.PositiveBigIntegerField("قیمت پایه (تومان)")
    discount_price = models.PositiveBigIntegerField(
        "قیمت با تخفیف (تومان - اختیاری)",
        blank=True,
        null=True,
        help_text="اگر محصول تخفیف ندارد این فیلد را خالی بگذارید."
    )
    
    fabric_details = models.CharField(
        "جنس و مشخصات دوخت",
        max_length=250,
        blank=True,
        help_text="مثال: کرپ گاباردین، آستردار و لمینت شده"
    )
    description = models.TextField("توضیحات کامل محصول", blank=True)
    
    # قابلیت شخصی‌دوزی (دوخت بر اساس سایز مشتری)
    allow_custom_measurements = models.BooleanField(
        "امکان سفارش‌دوزی بر اساس اندازه مشتری",
        default=True,
        help_text="اگر فعال باشد، باکس وارد کردن اندازه‌ها (دور سینه، قد و...) در صفحه محصول نمایش داده می‌شود."
    )
    custom_measurement_hint = models.CharField(
        "راهنمای اندازه‌گیری برای مشتری",
        max_length=250,
        default="در صورت تمایل به دوخت سفارشی، اندازه‌های دقیق (دور سینه، دور کمر، قد کت/شلوار) را بنویسید.",
        blank=True
    )
    
    is_active = models.BooleanField("نمایش در سایت", default=True)
    is_featured = models.BooleanField("نمایش در بخش ویژه صفحه اول", default=False)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "محصول"
        verbose_name_plural = "۲. محصولات"

    def clean(self):
        if self.discount_price is not None and self.base_price is not None:
            if self.discount_price >= self.base_price:
                raise ValidationError({"discount_price": "قیمت با تخفیف باید کمتر از قیمت پایه باشد."})
            if self.discount_price <= 0:
                raise ValidationError({"discount_price": "قیمت با تخفیف باید بیشتر از صفر باشد."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def has_discount(self):
        return bool(self.discount_price and self.discount_price < self.base_price)

    def get_effective_base_price(self):
        """قیمت پایه موثر (با احتساب تخفیف در صورت وجود)"""
        if self.has_discount:
            return self.discount_price
        return self.base_price

    @property
    def total_stock(self):
        return sum(v.stock for v in self.variants.filter(is_active=True))

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="محصول"
    )
    size_title = models.CharField(
        "سایز / عنوان متغیر",
        max_length=50,
        help_text="مثال: 36، 38، 40، 42، 44 یا دوخت سفارشی"
    )
    price_adjustment = models.PositiveBigIntegerField(
        "افزایش قیمت این سایز (تومان)",
        default=0,
        help_text="اگر این سایز (مثلاً بالای ۴۲) گران‌تر است، فقط مابه‌التفاوت را به تومان وارد کنید. در غیر این صورت 0 بگذارید."
    )
    stock = models.PositiveIntegerField("موجودی انبار", default=5)
    display_order = models.PositiveSmallIntegerField("ترتیب نمایش سایز", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "سایز و موجودی"
        verbose_name_plural = "سایزبندی و قیمت سایزها"
        constraints = [
            models.UniqueConstraint(fields=['product', 'size_title'], name='unique_product_size')
        ]

    def get_final_price(self):
        """محاسبه امن قیمت نهایی این سایز در سمت سرور"""
        return self.product.get_effective_base_price() + self.price_adjustment

    def __str__(self):
        if self.price_adjustment > 0:
            return f"{self.product.name} - سایز {self.size_title} (+{self.price_adjustment:,} تومان)"
        return f"{self.product.name} - سایز {self.size_title}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول"
    )
    image = models.ImageField(
        "تصویر گالری",
        upload_to="products/gallery/",
        validators=[validate_image_security]
    )
    alt_text = models.CharField("متن جایگزین (اختیاری)", max_length=150, blank=True)
    display_order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "تصویر گالری"
        verbose_name_plural = "گالری تصاویر بیشتر"

    def __str__(self):
        return f"تصویر {self.product.name}"