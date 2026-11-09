from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import SiteSetting
from catalog.models import Category, Product, ProductVariant
from .models import Order


class OrderAndCartSecurityTest(TestCase):
    def setUp(self):
        self.settings = SiteSetting.load()
        self.settings.shipping_cost = 70000
        self.settings.enable_two_stage_payment = True
        self.settings.deposit_percentage = 50
        self.settings.save()

        cat = Category.objects.create(name="کت")
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile("coat.jpg", small_gif, content_type="image/jpeg")
        self.product = Product.objects.create(
            category=cat,
            name="کت قهوه‌ای",
            base_price=4500000,
            main_image=img,
            allow_custom_measurements=True
        )
        self.variant_44 = ProductVariant.objects.create(
            product=self.product,
            size_title="44",
            price_adjustment=300000,  # قیمت نهایی می‌شود 4,800,000
            stock=3
        )

    def test_two_stage_deposit_order_calculation(self):
        """تست محاسبه دقیق ۵۰٪ بیعانه + هزینه ارسال و ذخیره اندازه‌های شخصی‌دوزی"""
        self.client.post(reverse('orders:cart_add'), {
            'variant_id': self.variant_44.id,
            'quantity': 1,
            'custom_measurements': 'دور سینه ۹۸، قد کت ۷۵'
        })

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'مینا حسینی',
            'phone': '09121234567',
            'province': 'تهران',
            'city': 'تهران',
            'address': 'جنت آباد جنوبی، خیابان اصلی، پلاک ۱۰',
            'payment_type': 'deposit',
        })

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        # قیمت سایز ۴۴: 4,800,000 | هزینه ارسال: 70,000 | کل فاکتور: 4,870,000
        self.assertEqual(order.total_amount, 4870000)
        # ۵۰ درصد از 4,800,000 می‌شود 2,400,000 + 70,000 ارسال = 2,470,000
        self.assertEqual(order.payable_now, 2470000)
        self.assertEqual(order.items.first().custom_measurements, 'دور سینه ۹۸، قد کت ۷۵')